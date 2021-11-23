from RsInstrument.RsInstrument import RsInstrument





class RSCurrentGenerator:
    def __init__(self):
        resource_string_4 = 'ASRL7::INSTR'  # USB-TMC (Test and Measurement Class)
        self.instr = RsInstrument(resource_string_4, True, False)
        self.idn = self.instr.query_str('*IDN?')
        print(f"\nHello, I am: '{self.idn}'")
        print(f'Instrument full name: {self.instr.full_instrument_model_name}')

    def Config_Currents(self,I_x,I_y,I_z):
        self.instr.write_str('INST OUT1')
        self.instr.write_int('CURR', I_x)
        self.instr.write_str('INST OUT2')
        self.instr.write_int('CURR', I_y)
        self.instr.write_str('INST OUT3')
        self.instr.write_int('CURR', I_z)

    def CloseInstr(self):
        # Close the session
        self.instr.close()

if __name__ == "__main__":
    rscg = RSCurrentGenerator()
    rscg.Config_Currents(0.2,0.05,0.1)

