from __future__ import annotations
from enum import Enum

import smbus2

class INA226:
    
    # Registers
    CONFIGURATION_REG = 0x00
    SHUNT_VOLTAGE_REG = 0x01
    BUS_VOLTAGE_REG   = 0x02
    POWER_REG         = 0x03
    CURRENT_REG       = 0x04
    CALIBRATION_REG   = 0x05
    MASK_ENABLE_REG   = 0x06
    ALERT_LIMIT_REG   = 0x07
    MANUFACTURER_REG  = 0xFE
    DIE_ID_REG        = 0xFF

    # CONFIGURATION MASKS
    CONF_RESET_MASK   = 0x8000
    CONF_AVERAGE_MASK = 0x0E00
    CONF_BUSVC_MASK   = 0x01C0
    CONF_SHUNTVC_MASK = 0x0038
    CONF_MODE_MASK    = 0x0007

    # Number of average
    class Average(Enum):
        N1    = 0
        N4    = 1
        N16   = 2
        N64   = 3
        N128  = 4
        N256  = 5
        N512  = 6
        N1024 = 7

        def num(self) -> int:
            if self.value == 0:
                return 1
            if self.value == 1:
                return 4
            if self.value == 2:
                return 16
            if self.value == 3:
                return 64
            if self.value == 4:
                return 128
            if self.value == 5:
                return 256
            if self.value == 6:
                return 512
            if self.value == 7:
                return 1024

    # Conversion time
    class ConversionTime(Enum):
        T140us = 0
        T204us = 1
        T332us = 2
        T588us = 3
        T1100us = 4
        T2116us = 5
        T4156us = 6
        T8244us = 7

        def us(self) -> int:
            """
            get actual micro seconds of this object.
            """
            if self.value == 0:
                return 140
            if self.value == 1:
                return 204
            if self.value == 2:
                return 332
            if self.value == 3:
                return 588
            if self.value == 4:
                return 1100
            if self.value == 5:
                return 2116
            if self.value == 6:
                return 4156
            if self.value == 7:
                return 8244


    # Current LSB
    # calculate this value by (max expected current [A]) / 2^15
    __current_lsb_A: float = 0.0

    # Functions

    def __init__(self, i2c: smbus2.SMBus, addr: int) -> None:
        self.__i2c = i2c
        self.__addr = addr
    
    def __read_16bit(self, reg_addr: int) -> int:
        high_byte, low_byte = self.__i2c.read_i2c_block_data(
            self.__addr, reg_addr, 2
        )
        return (high_byte << 8) + low_byte

    def __write_16bit(self, reg_addr: int, data: int) -> None:
        high_byte = (data >> 8) & 0xff
        low_byte  = data & 0xff
        self.__i2c.write_i2c_block_data(
            self.__addr, reg_addr, [high_byte, low_byte]
        )

    def __convert_two_complement_to_decimal(self, val: int, bit_len: int) -> int:
        val &= ((1 << bit_len) - 1)     # mask bit_len digit
        msb = val >> (bit_len - 1)      # extract most significant bit (sign bit)
        if msb == 1:                    # if msb == 1, it is negative value
            abs = (1 << bit_len) - val  # get absolute value
            return -abs                 # add minus sign
        else:
            return val
    # core functions
    
    def get_shunt_voltage_mV(self) -> float:
        val = self.__read_16bit(self.SHUNT_VOLTAGE_REG)
        val = self.__convert_two_complement_to_decimal(val, 16)
        return val * 2.5e-3
        
    def get_bus_voltage_V(self) -> float:
        val = self.__read_16bit(self.BUS_VOLTAGE_REG)
        return val * 1.25e-3
    
    def get_power_W(self) -> float:
        val = self.__read_16bit(self.POWER_REG)
        val = self.__convert_two_complement_to_decimal(val, 16)
        return val * 25 * self.__current_lsb_A
    
    def get_current_A(self) -> float:
        val = self.__read_16bit(self.CURRENT_REG)
        val = self.__convert_two_complement_to_decimal(val, 16)
        return val * self.__current_lsb_A
    
    # configuration
    
    def reset(self) -> None:
        mask = self.__read_16bit(self.CONFIGURATION_REG)
        mask |= self.CONF_RESET_MASK
        self.__write_16bit(self.CONFIGURATION_REG, mask)
        self.__current_lsb_A = 0.0  # reset calibration

    def set_average(self, avg: Average) -> None:
        mask = self.__read_16bit(self.CONFIGURATION_REG)
        mask &= ~self.CONF_AVERAGE_MASK
        mask |= (avg.value << 9)
        self.__write_16bit(self.CONFIGURATION_REG, mask)
    
    def get_average(self) -> int:
        mask = self.__read_16bit(self.CONFIGURATION_REG)
        mask &= self.CONF_AVERAGE_MASK
        mask >>= 9
        avg = self.Average(mask)
        return avg.num()
    
    def set_bus_voltage_conversion_time(self, conv_time: ConversionTime) -> None:
        mask = self.__read_16bit(self.CONFIGURATION_REG)
        mask &= ~self.CONF_BUSVC_MASK
        mask |= (conv_time.value << 6)
        self.__write_16bit(self.CONFIGURATION_REG, mask)
    
    def get_bus_voltage_conversion_time_us(self) -> int:
        mask = self.__read_16bit(self.CONFIGURATION_REG)
        mask &= self.CONF_BUSVC_MASK
        mask >>= 6
        conv_time = self.ConversionTime(mask)
        return conv_time.us()

    def set_shunt_voltage_conversion_time(self, conv_time: ConversionTime) -> None:
        mask = self.__read_16bit(self.CONFIGURATION_REG)
        mask &= ~self.CONF_SHUNTVC_MASK
        mask |= (conv_time.value << 3)
        self.__write_16bit(self.CONFIGURATION_REG, mask)

    def get_shunt_voltage_conversion_time_us(self) -> int:
        mask = self.__read_16bit(self.CONFIGURATION_REG)
        mask &= self.CONF_SHUNTVC_MASK
        mask >>= 3
        conv_time = self.ConversionTime(mask)
        return conv_time.us()

    # calibration

    def set_calibration(self, current_lsb_A: float, shunt_ohm: float) -> int:
        """
        Set calibration register value

        Parameters
        ----------
        current_lsb_A: 
            Calculate this value by (max expected current [A]) / 2^15
        shunt_ohm:
            Resistance of the shunt register [Ohm]
        """
        if current_lsb_A <= 0.0 or shunt_ohm <= 0.0:  # avoid zero division
            return 0
        
        cal = 0.00512 / current_lsb_A / shunt_ohm

        if cal > 65535:
            return 0

        self.__current_lsb_A = current_lsb_A
        self.__write_16bit(self.CALIBRATION_REG, int(cal))
        return int(cal)

    def get_calibration_reg(self) -> int:
        val = self.__read_16bit(self.CALIBRATION_REG)
        return val
    
    def get_current_lsb_A(self) -> float:
        return self.__current_lsb_A

    # meta information

    def get_manufacturer_id(self) -> int:
        """
        should return 0x5449
        """
        return self.__read_16bit(self.MANUFACTURER_REG)

    def get_die_id(self) -> int:
        """
        should return 0x2260
        """
        return self.__read_16bit(self.DIE_ID_REG)
