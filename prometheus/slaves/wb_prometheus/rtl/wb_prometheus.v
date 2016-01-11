//wb_prometheus.v
/*
Distributed under the MIT license.
Copyright (c) 2015 Dave McCoy (dave.mccoy@cospandesign.com)

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/

/*
  Set the Vendor ID (Hexidecimal 64-bit Number)
  SDB_VENDOR_ID:0x800000000000C594

  Set the Device ID (Hexcidecimal 32-bit Number)
  SDB_DEVICE_ID:0x800000000000C594

  Set the version of the Core XX.XXX.XXX Example: 01.000.000
  SDB_CORE_VERSION:00.000.001

  Set the Device Name: 19 UNICODE characters
  SDB_NAME:wb_prometheus

  Set the class of the device (16 bits) Set as 0
  SDB_ABI_CLASS:0

  Set the ABI Major Version: (8-bits)
  SDB_ABI_VERSION_MAJOR:0x0F

  Set the ABI Minor Version (8-bits)
  SDB_ABI_VERSION_MINOR:0

  Set the Module URL (63 Unicode Characters)
  SDB_MODULE_URL:http://www.example.com

  Set the date of module YYYY/MM/DD
  SDB_DATE:2015/12/29

  Device is executable (True/False)
  SDB_EXECUTABLE:True

  Device is readable (True/False)
  SDB_READABLE:True

  Device is writeable (True/False)
  SDB_WRITEABLE:True

  Device Size: Number of Registers
  SDB_SIZE:3
*/


module wb_prometheus (
  input               clk,
  input               rst,

  //Add signals to control your device here

  //Wishbone Bus Signals
  input               i_wbs_we,
  input               i_wbs_cyc,
  input       [3:0]   i_wbs_sel,
  input       [31:0]  i_wbs_dat,
  input               i_wbs_stb,
  output  reg         o_wbs_ack,
  output  reg [31:0]  o_wbs_dat,
  input       [31:0]  i_wbs_adr,

  output  reg         o_wbs_int,

  //Host Interface

  //Incomming Interface
  output              o_ingress_ready,
  input               i_ingress_activate,
  output      [23:0]  o_ingress_packet_size,
  output      [31:0]  o_ingress_data,
  input               i_ingress_strobe,

  //Outgoing Interface
  output      [1:0]   o_egress_ready,
  input       [1:0]   i_egress_activate,
  output      [23:0]  o_egress_size,
  input       [31:0]  i_egress_data,
  input               i_egress_strobe,

  //Phy Interface
  output              o_gpif_clk,

  output              o_cs_n,
  output              o_oe_n,
  output              o_we_n,
  output              o_re_n,
  output              o_pkt_end_n,
  inout       [31:0]  io_data,

  //DMA Flags
  input               i_in_rdy,
  input               i_out_rdy,
  output      [1:0]   o_socket_addr,
  output              o_gpif_int_n,

  output      [7:0]   o_debug
);

//Local Parameters
localparam     CONTROL  = 32'h00000000;
localparam     STATUS   = 32'h00000001;

//Local Registers/Wires
reg                 r_usb3_data_size_sel;
wire  [7:0]         w_debug;
//Submodules
fx3_bus #(
  .ADDRESS_WIDTH        (8                      )
) fx3 (

  .clk                  (clk                    ),
  .rst                  (rst                    ),

  .o_gpif_clk           (o_gpif_clk             ),
  .io_data              (io_data                ),

  .o_cs_n               (o_cs_n                 ),
  .o_oe_n               (o_oe_n                 ),
  .o_we_n               (o_we_n                 ),
  .o_re_n               (o_re_n                 ),
  .o_pkt_end_n          (o_pkt_end_n            ),


  .i_in_rdy             (i_in_rdy               ),
  .i_out_rdy            (i_out_rdy              ),

  .o_socket_addr        (o_socket_addr          ),
  .o_gpif_int_n         (o_gpif_in_n            ),

//Configuration
  .i_usb3_data_size_sel (r_usb3_data_size_sel   ),

//Write side FIFO interface
  .o_ingress_ready      (o_ingress_ready        ),
  .i_ingress_activate   (i_ingress_activate     ),
  .o_ingress_packet_size(o_ingress_packet_size  ),
  .o_ingress_data       (o_ingress_data         ),
  .i_ingress_strobe     (i_ingress_strobe       ),

//Read side FIFO interface
  .o_egress_ready       (o_egress_ready         ),
  .i_egress_activate    (i_egress_activate      ),
  .o_egress_size        (o_egress_size          ),
  .i_egress_data        (i_egress_data          ),
  .i_egress_strobe      (i_egress_strobe        ),


  .o_debug              (o_debug                )
);

//Asynchronous Logic
//Synchronous Logic

always @ (posedge clk) begin
  if (rst) begin
    o_wbs_dat <= 32'h0;
    o_wbs_ack <= 0;
    o_wbs_int <= 0;
  end

  else begin
    //when the master acks our ack, then put our ack down
    if (o_wbs_ack && ~i_wbs_stb)begin
      o_wbs_ack <= 0;
    end

    if (i_wbs_stb && i_wbs_cyc) begin
      //master is requesting somethign
      if (!o_wbs_ack) begin
        if (i_wbs_we) begin
          //write request
          case (i_wbs_adr)
            CONTROL: begin
                $display("ADDR: %h user wrote %h", i_wbs_adr, i_wbs_dat);
            end
            STATUS: begin
                $display("ADDR: %h user wrote %h", i_wbs_adr, i_wbs_dat);
            end
            default: begin
            end
          endcase
        end
        else begin
          //read request
          case (i_wbs_adr)
            CONTROL: begin
              $display("user read %h", CONTROL);
              o_wbs_dat <= CONTROL;
            end
            STATUS: begin
              $display("user read %h", STATUS);
              o_wbs_dat <= STATUS;
            end
            default: begin
            end
          endcase
        end
      o_wbs_ack <= 1;
    end
    end
  end
end

endmodule
