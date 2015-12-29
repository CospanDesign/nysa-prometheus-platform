/*
 * The nice thing about defines that are not possible with parameters is that
 * you can pull defines to an external file and have all the defines in one
 * place. This can be accomplished with parameters and UCF files but that
 * would be vendor specific
 */

`define FX3_READ_START_LATENCY    1
`define FX3_WRITE_FULL_LATENCY    4

`include "project_include.v"



module fx3_bus # (
parameter           ADDRESS_WIDTH = 8   //128 coincides with the maximum DMA
                                        //packet size for USB 2.0
                                        //256 coincides with the maximum DMA
                                        //packet size for USB 3.0 since the 512
                                        //will work for both then the FIFOs will
                                        //be sized for this

)(
input               clk,
input               rst,

//Phy Interface
inout       [31:0]  io_data,

output              o_oe_n,
output              o_we_n,
output              o_re_n,
output              o_pkt_end_n,

input               i_in_rdy,

input               i_out_rdy,

output      [1:0]   o_socket_addr,


//Master Interface
input               i_master_ready,

output      [7:0]   o_command,
output      [7:0]   o_flag,
output      [31:0]  o_rw_count,
output      [31:0]  o_address,
output              o_command_rdy_stb,

input       [7:0]   i_status,
input       [31:0]  i_read_size,
input               i_status_rdy_stb,
input       [31:0]  i_address,        //Calculated end address, this can be
                                      //used to verify that the mem was
                                      //calculated correctly

//Write side FIFO interface
output              o_wpath_ready,
input               i_wpath_activate,
output      [23:0]  o_wpath_packet_size,
output      [31:0]  o_wpath_data,
input               i_wpath_strobe,


//Read side FIFO interface
output      [1:0]   o_rpath_ready,
input       [1:0]   i_rpath_activate,
output      [23:0]  o_rpath_size,
input       [31:0]  i_rpath_data,
input               i_rpath_strobe
);

//Local Parameters
localparam          IDLE;
//Registers/Wires
wire                w_output_enable;
wire                w_read_enable;
wire                w_write_enable;
wire                w_packet_end;

wire        [31:0]  w_in_data;
wire        [31:0]  w_out_data;
wire                w_data_valid;

wire        [23:0]  w_packet_size;
wire                w_read_flow_cntrl;

//In Path Control
wire                w_in_path_enable;
wire                w_in_path_busy;
wire                w_in_path_finished;

//In Command Path
wire                w_in_path_cmd_enable;
wire                w_in_path_cmd_busy;
wire                w_in_path_cmd_finished;

//Out Path Control
wire                w_out_path_ready;
wire                w_out_path_enable;
wire                w_out_path_busy;
wire                w_out_path_finished;


reg         [3:0]   state;

//Submodules
//Asynchronous Logic
//Synchronous Logic

always @ (posedge clk) begin
  if (rst) begin
    state         <=  IDLE;
  end
  else begin
    case (state)
      IDLE: begin
      end
      default: begin
      end
    endcase
  end
end
endmodule

