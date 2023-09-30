from __future__ import annotations
from enum import Enum

import smbus2

class INA228:
    
    # Registers
    CONFIG_REG          = 0x00
    ADC_CONFIG_REG      = 0x01
    SHUNT_CAL_REG       = 0x02
    SHUNT_TEMPCO_REG    = 0x03
    VSHUNT_REG          = 0x04
    VBUS_REG            = 0x05
    DIETEMP_REG         = 0x06
    CURRENT_REG         = 0x07
    POWER_REG           = 0x08
    ENERGY_REG          = 0x09
    CHARGE_REG          = 0x0A
    DIAG_ALERT_REG      = 0x0B
    SOVL_REG            = 0x0C
    SUVL_REG            = 0x0D
    BOVL_REG            = 0x0E
    BUVL_REG            = 0x0F
    TEMP_LIMIT_REG      = 0x10
    PWR_LIMIT_REG       = 0x11
    MANUFACTURER_ID_REG = 0xFE
    DEVICE_ID_REG       = 0xFF

    # CONFIG MASKS
    RST_MASK       = (0b1 << 15)
    RSTACC_MASK    = (0b1 << 14)
    CONVDLY_MASK   = (0b11111111 << 6)
    TEMPCOMP_MASK  = (0b1 << 5)
    ADCRANGE_MASK  = (0b1 << 4)

    # ADC_CONFIG MASKS
    MODE_MASK   = (0b1111 << 12)
    VBUSCT_MASK = (0b111 << 9)
    VSHCT_MASK  = (0b111 << 6)
    VTCT_MASK   = (0b111 << 3)
    AVG_MASK    = (0b111)

    # DIAG_ALERT MASKS
    ALATCH_MASK    = (0b1 << 15)
    CNVR_MASK      = (0b1 << 14)
    SLOWALERT_MASK = (0b1 << 13)
    APOL_MASK      = (0b1 << 12)
    ENERGYOF_MASK  = (0b1 << 11)
    CHARGEOF_MASK  = (0b1 << 10)
    MATHOF_MASK    = (0b1 << 9)
    TMPOL_MASK     = (0b1 << 7)
    SHNTOL_MASK    = (0b1 << 6)
    SHNTUL_MASK    = (0b1 << 5)
    BUSOL_MASK     = (0b1 << 4)
    BUSUL_MASK     = (0b1 << 3)
    POL_MASK       = (0b1 << 2)
    CNVRF_MASK     = (0b1 << 1)
    MEMSTAT_MASK   = (0b1)

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
        T50us = 0
        T84us = 1
        T150us = 2
        T280us = 3
        T540us = 4
        T1052us = 5
        T2074us = 6
        T4120us = 7

        def us(self) -> int:
            """
            get actual micro seconds of this object.
            """
            if self.value == 0:
                return 50
            if self.value == 1:
                return 84
            if self.value == 2:
                return 150
            if self.value == 3:
                return 280
            if self.value == 4:
                return 540
            if self.value == 5:
                return 1052
            if self.value == 6:
                return 2074
            if self.value == 7:
                return 4120
    
    # Mode
    class Mode(Enum):
        Shutdown = 0x0
        Triggered_V = 0x1
        Triggered_I = 0x2
        Triggered_V_I = 0x3
        Triggered_T = 0x4
        Triggered_V_T = 0x5
        Triggered_I_T = 0x6
        Triggered_V_I_T = 0x7
        Continuous_V = 0x9
        Continuous_I = 0xA
        Continuous_V_I = 0xB
        Continuous_T = 0xC
        Continuous_V_T = 0xD
        Continuous_I_T = 0xE
        Continuous_V_I_T = 0xF

    # Current LSB
    # calculate this value by (max expected current [A]) / 2^19
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

    def __read_24bit(self, reg_addr: int) -> int:
        b2, b1, b0 = self.__i2c.read_i2c_block_data(
            self.__addr, reg_addr, 3
        )
        return (b2 << 16) + (b1 << 8) + b0

    def __read_40bit(self, reg_addr: int) -> int:
        b4, b3, b2, b1, b0 = self.__i2c.read_i2c_block_data(
            self.__addr, reg_addr, 5
        )
        return (b4 << 32) + (b3 << 24) + (b2 << 16) + (b1 << 8) + b0

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
        val = self.__read_24bit(self.VSHUNT_REG)
        val = (val >> 4)
        val = self.__convert_two_complement_to_decimal(val, 20)
        adcrange = self.get_adc_range()
        if adcrange == 0:
            return val * 312.5e-6
        elif adcrange == 1:
            return val * 78.125e-6
        
    def get_bus_voltage_V(self) -> float:
        val = self.__read_24bit(self.VBUS_REG)
        val = (val >> 4)
        return val * 195.3125e-6
    
    def get_temperature_C(self) -> float:
        val = self.__read_16bit(self.DIETEMP_REG)
        val = self.__convert_two_complement_to_decimal(val, 16)
        return val * 7.8125e-3
        
    def get_current_A(self) -> float:
        val = self.__read_24bit(self.CURRENT_REG)
        val = (val >> 4)
        val = self.__convert_two_complement_to_decimal(val, 20)
        return val * self.__current_lsb_A

    def get_power_W(self) -> float:
        val = self.__read_24bit(self.POWER_REG)
        return 3.2 * self.__current_lsb_A * val

    def get_energy_J(self) -> float:
        val = self.__read_40bit(self.ENERGY_REG)
        return 16 * 3.2 * self.__current_lsb_A * val
    
    def get_charge_C(self) -> float:
        val = self.__read_40bit(self.CHARGE_REG)
        val = self.__convert_two_complement_to_decimal(val, 40)
        return self.__current_lsb_A * val
    
    # configuration
    
    def reset(self) -> None:
        mask = self.__read_16bit(self.CONFIG_REG)
        mask |= self.RST_MASK
        self.__write_16bit(self.CONFIG_REG, mask)
        self.__current_lsb_A = 0.0  # reset calibration

    def reset_energy_and_charge(self) -> None:
        mask = self.__read_16bit(self.CONFIG_REG)
        mask |= self.RSTACC_MASK
        self.__write_16bit(self.CONFIG_REG, mask)
    
    def set_conv_delay_ms(self, delay_ms: int) -> bool:
        if delay_ms < 0 or delay_ms > 510 or delay_ms % 2 == 1:
            return False
        mask = self.__read_16bit(self.CONFIG_REG)
        mask &= ~self.CONVDLY_MASK
        mask |= ((delay_ms / 2) << 6)
        self.__write_16bit(self.CONFIG_REG, mask)
        return True

    def get_conv_delay_ms(self) -> int:
        mask = self.__read_16bit(self.CONFIG_REG)
        mask &= self.CONVDLY_MASK
        mask >> 6
        return mask * 2

    # TODO: TEMPCOMP

    def set_adc_range(self, adcrange: int) -> None:
        """
        adcrange: int
            0 = ±163.84mV, 1 = ±40.96mV
        """
        mask = self.__read_16bit(self.CONFIG_REG)
        mask &= ~self.ADCRANGE_MASK
        mask |= (adcrange << 4)
        self.__write_16bit(self.CONFIG_REG, mask)
    
    def get_adc_range(self) -> int:
        """
        0 = ±163.84mV, 1 = ±40.96mV
        """
        mask = self.__read_16bit(self.CONFIG_REG)
        mask &= self.ADCRANGE_MASK
        val = (mask >> 4)
        return val

    # ADC configuration

    def set_mode(self, mode: Mode) -> None:
        mask = self.__read_16bit(self.ADC_CONFIG_REG)
        mask &= ~self.MODE_MASK
        mask |= (mode.value << 12)
        self.__write_16bit(self.ADC_CONFIG_REG, mask)

    def get_mode(self) -> Mode:
        mask = self.__read_16bit(self.ADC_CONFIG_REG)
        mask &= self.MODE_MASK
        mask >>= 12
        mode = self.Mode(mask)
        return mode
    
    def set_bus_voltage_conversion_time(self, conv_time: ConversionTime) -> None:
        mask = self.__read_16bit(self.ADC_CONFIG_REG)
        mask &= ~self.VBUSCT_MASK
        mask |= (conv_time.value << 9)
        self.__write_16bit(self.ADC_CONFIG_REG, mask)
    
    def get_bus_voltage_conversion_time_us(self) -> int:
        mask = self.__read_16bit(self.ADC_CONFIG_REG)
        mask &= self.VBUSCT_MASK
        mask >>= 9
        conv_time = self.ConversionTime(mask)
        return conv_time.us()

    def set_shunt_voltage_conversion_time(self, conv_time: ConversionTime) -> None:
        mask = self.__read_16bit(self.ADC_CONFIG_REG)
        mask &= ~self.VSHCT_MASK
        mask |= (conv_time.value << 6)
        self.__write_16bit(self.ADC_CONFIG_REG, mask)

    def get_shunt_voltage_conversion_time_us(self) -> int:
        mask = self.__read_16bit(self.ADC_CONFIG_REG)
        mask &= self.VSHCT_MASK
        mask >>= 6
        conv_time = self.ConversionTime(mask)
        return conv_time.us()
    
    def set_temperature_conversion_time(self, conv_time: ConversionTime) -> None:
        mask = self.__read_16bit(self.ADC_CONFIG_REG)
        mask &= ~self.VTCT_MASK
        mask |= (conv_time.value << 3)
        self.__write_16bit(self.ADC_CONFIG_REG, mask)

    def get_temperature_conversion_time_us(self) -> int:
        mask = self.__read_16bit(self.ADC_CONFIG_REG)
        mask &= self.VTCT_MASK
        mask >>= 3
        conv_time = self.ConversionTime(mask)
        return conv_time.us()

    def set_average(self, avg: Average) -> None:
        mask = self.__read_16bit(self.ADC_CONFIG_REG)
        mask &= ~self.AVG_MASK
        mask |= avg.value
        self.__write_16bit(self.ADC_CONFIG_REG, mask)
    
    def get_average(self) -> int:
        mask = self.__read_16bit(self.ADC_CONFIG_REG)
        mask &= self.AVG_MASK
        avg = self.Average(mask)
        return avg.num()

    # calibration

    def set_calibration(self, max_current_A: float, shunt_ohm: float) -> int:
        if max_current_A <= 0.0 or shunt_ohm <= 0.0:  # avoid zero division
            return 0
        
        current_lsb_temp = max_current_A / 2**19
        shunt_cal = int(13107.2 * 10**6 * current_lsb_temp * shunt_ohm)

        if self.get_adc_range() == 1:
            shunt_cal = shunt_cal * 4

        if shunt_cal > 65535:
            return 0

        self.__current_lsb_A = shunt_cal / 13107.2 / 10**6 / shunt_ohm
        self.__write_16bit(self.SHUNT_CAL_REG, shunt_cal)
        return shunt_cal

    def get_calibration_reg(self) -> int:
        val = self.__read_16bit(self.SHUNT_CAL_REG)
        return val
    
    def get_current_lsb_A(self) -> float:
        return self.__current_lsb_A

    # meta information

    def get_manufacturer_id(self) -> int:
        """
        should return 0x5449
        """
        return self.__read_16bit(self.MANUFACTURER_ID_REG)

    def get_device_id(self) -> int:
        """
        should return 0x2281
        """
        return self.__read_16bit(self.DEVICE_ID_REG)
