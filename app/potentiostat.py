import time
import board
import busio
import adafruit_mcp4725
import smbus2


# Create a custom MCP4725 device object with address 0x60
class MyMCP4725(adafruit_mcp4725.MCP4725):
    def __init__(self, i2c):
        super().__init__(i2c, address=0x60)


# Function to read ADC value
def read_adc(channel):
    if channel == 0:
        config = ADS1115_REG_CONFIG_OS_SINGLE | ADS1115_REG_CONFIG_MUX_SINGLE_0 | ADS1115_REG_CONFIG_PGA_6_144V
    elif channel == 2:
        config = ADS1115_REG_CONFIG_OS_SINGLE | ADS1115_REG_CONFIG_MUX_SINGLE_2 | ADS1115_REG_CONFIG_PGA_6_144V
    else:
        raise ValueError("Invalid channel number")

    # Send config data
    adc_bus.write_i2c_block_data(ADS1115_I2C_ADDRESS, ADS1115_REG_POINTER_CONFIG, [(config >> 8) & 0xFF, config & 0xFF])

    # Wait for conversion to complete
    time.sleep(0.1)

    # Read conversion result
    data = adc_bus.read_i2c_block_data(ADS1115_I2C_ADDRESS, ADS1115_REG_POINTER_CONVERT, 2)

    # Convert data to 16-bit signed integer
    value = (data[0] << 8) | data[1]
    if value > 32767:
        value -= 65536

    return value


# Function to convert ADC value to voltage
def adc_to_voltage(adc_value, offset, scaling_factor):
    return (adc_value - offset) * scaling_factor


# Create I2C bus for ADC
adc_bus = smbus2.SMBus(1)

# Initialize I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

# ADS1115 address
ADS1115_I2C_ADDRESS = 0x48

# Register addresses
ADS1115_REG_POINTER_CONVERT = 0x00
ADS1115_REG_POINTER_CONFIG = 0x01

# Configuration values for ADC
ADS1115_REG_CONFIG_OS_SINGLE = 0x8000  # Start a single conversion
ADS1115_REG_CONFIG_MUX_SINGLE_0 = 0x4000  # Channel 0
ADS1115_REG_CONFIG_MUX_SINGLE_2 = 0x6000  # Channel 2
ADS1115_REG_CONFIG_PGA_6_144V = 0x0000  # +/-6.144V

# Create an instance of the custom MCP4725 object
dac = MyMCP4725(i2c)

# Set DAC output voltage to 0V
dac.raw_value = 0
print("Output voltage set to 0V")

# Delay to ensure DAC settles
time.sleep(1)

# Read ADC values to determine offsets for both channels
offset_channel_0 = read_adc(0)

time.sleep(1)

offset_channel_2 = read_adc(2)

time.sleep(1)

print("Offset for Channel 0:", offset_channel_0)
print("Offset for Channel 2:", offset_channel_2)

time.sleep(1)

# Initialize I2C bus for DAC
i2c = busio.I2C(board.SCL, board.SDA)

# Create MCP4725 DAC object
dac = adafruit_mcp4725.MCP4725(i2c, address=0x60)

# Adjust values for your setup
VREF = 5.15  # Reference voltage
TARGET_MIN_V = 0  # Desired minimum voltage
TARGET_MAX_V = 0  # Desired maximum voltage
NUM_STEPS = 0  # Number of steps for the sweep
DELAY = 3  # Delay between voltage steps (in seconds)
NUM_READINGS = 5  # Number of readings to take at each step

voltage_step = 0


def prime_potentiostat(event: dict) -> None:
    global TARGET_MIN_V, TARGET_MAX_V, NUM_STEPS, voltage_step
    
    TARGET_MIN_V = event.get("start_voltage")
    TARGET_MAX_V = event.get("end_voltage")
    voltage_step = event.get("voltage_step")

    # Calculate the number of steps
    NUM_STEPS = int((TARGET_MAX_V - TARGET_MIN_V) / voltage_step)


def get_measurements() -> tuple[float, float]:
    # Sweep voltage from TARGET_MIN_V to TARGET_MAX_V in steps
    for i in range(NUM_STEPS + 1):  # Add 1 to include the last step
        # Calculate the target voltage for the current step
        target_voltage = TARGET_MIN_V + i * voltage_step
        
        # Calculate the DAC value corresponding to the target voltage
        dac_value = int(target_voltage * (4150 / VREF))
        
        # Set the initial DAC value
        dac.raw_value = dac_value
        
        # Print the target voltage and the corresponding DAC value
        print("Step:", i)
        print("Target Voltage:", target_voltage, "V")
        
        time.sleep(1)
        # Adjust DAC value based on feedback from Channel 2
        while True:
            # Read voltage from Channel 2
            adc_value_channel_2 = read_adc(2)
            voltage_channel_2 = adc_to_voltage(adc_value_channel_2, offset_channel_2, 6.4 / 32767.0)
            time.sleep(0.2)
            # Check if the measured voltage matches the target voltage
            if abs(voltage_channel_2 - target_voltage) > 0.05:  # Tolerance of 50mV
                break
            time.sleep(0.2)
            # Adjust DAC value based on the comparison
            if voltage_channel_2 > target_voltage:
                dac.raw_value -= 10  # Decrease DAC value
            else:
                dac.raw_value += 10  # Increase DAC value
            
            # Ensure DAC value stays within bounds
            dac.raw_value = max(0, min(4095, dac.raw_value))
            
            # Add a short delay before rechecking
            time.sleep(0.2)
        
        # Take multiple readings from ADC channels 0
        readings_channel_0 = []
        for _ in range(NUM_READINGS):
            adc_value_0 = read_adc(0)
            readings_channel_0.append(adc_value_0)
            time.sleep(0.5)
        
        # Calculate average voltage for Channel 0
        avg_voltage_0 = sum(readings_channel_0) / len(readings_channel_0)
        
        # Convert ADC value to voltage for Channel 0
        voltage_0 = adc_to_voltage(avg_voltage_0, offset_channel_0, 8 / 32767.0)
        
        # Calculate current for Channel 2 (current measurement)
        current_2 = (voltage_channel_2 / 2.5) * 5  # Voltage divider formula to calculate current in mA
        
        # Print voltage values
        yield current_2, voltage_0
        
        # Wait for the specified delay
        time.sleep(DELAY)

    # Ensure the DAC output returns to 0V for safety
    dac.raw_value = 0
