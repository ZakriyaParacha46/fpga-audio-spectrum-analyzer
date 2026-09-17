# --- Minimal constraints: audio_driver + waveform_display + clocking wizard ---

# 100 MHz onboard clock
set_property -dict { PACKAGE_PIN W5   IOSTANDARD LVCMOS33 } [get_ports { clk }];

# Center button as synchronous reset
set_property -dict { PACKAGE_PIN U18  IOSTANDARD LVCMOS33 } [get_ports { reset }];

# Filter cutoff control: sw0 selects lowpass(0)/highpass(1), btnL/btnR step it
set_property -dict { PACKAGE_PIN V17  IOSTANDARD LVCMOS33 } [get_ports { sw0 }];
set_property -dict { PACKAGE_PIN W19  IOSTANDARD LVCMOS33 } [get_ports { btnL }];
set_property -dict { PACKAGE_PIN T17  IOSTANDARD LVCMOS33 } [get_ports { btnR }];

# XADC analog input pair -> JXADC pin 1 (XA1_P) and pin 7 (XA1_N)
set_property -dict { PACKAGE_PIN J3   IOSTANDARD LVCMOS33 } [get_ports { vauxp6 }]; # XA1_P
set_property -dict { PACKAGE_PIN K3   IOSTANDARD LVCMOS33 } [get_ports { vauxn6 }]; # XA1_N

# VGA connector (4 bits per color channel + sync)
set_property -dict { PACKAGE_PIN G19  IOSTANDARD LVCMOS33 } [get_ports { vgaRed[0] }];
set_property -dict { PACKAGE_PIN H19  IOSTANDARD LVCMOS33 } [get_ports { vgaRed[1] }];
set_property -dict { PACKAGE_PIN J19  IOSTANDARD LVCMOS33 } [get_ports { vgaRed[2] }];
set_property -dict { PACKAGE_PIN N19  IOSTANDARD LVCMOS33 } [get_ports { vgaRed[3] }];
set_property -dict { PACKAGE_PIN J17  IOSTANDARD LVCMOS33 } [get_ports { vgaGreen[0] }];
set_property -dict { PACKAGE_PIN H17  IOSTANDARD LVCMOS33 } [get_ports { vgaGreen[1] }];
set_property -dict { PACKAGE_PIN G17  IOSTANDARD LVCMOS33 } [get_ports { vgaGreen[2] }];
set_property -dict { PACKAGE_PIN D17  IOSTANDARD LVCMOS33 } [get_ports { vgaGreen[3] }];
set_property -dict { PACKAGE_PIN N18  IOSTANDARD LVCMOS33 } [get_ports { vgaBlue[0] }];
set_property -dict { PACKAGE_PIN L18  IOSTANDARD LVCMOS33 } [get_ports { vgaBlue[1] }];
set_property -dict { PACKAGE_PIN K18  IOSTANDARD LVCMOS33 } [get_ports { vgaBlue[2] }];
set_property -dict { PACKAGE_PIN J18  IOSTANDARD LVCMOS33 } [get_ports { vgaBlue[3] }];
set_property -dict { PACKAGE_PIN P19  IOSTANDARD LVCMOS33 } [get_ports { Hsync }];
set_property -dict { PACKAGE_PIN R19  IOSTANDARD LVCMOS33 } [get_ports { Vsync }];
