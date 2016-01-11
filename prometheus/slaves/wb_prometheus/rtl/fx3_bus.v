/*
 * The nice thing about defines that are not possible with parameters is that
 * you can pull defines to an external file and have all the defines in one
 * place. This can be accomplished with parameters and UCF files but that
 * would be vendor specific
 */

`define FX3_READ_START_LATENCY    1
`define FX3_READ_END_DELAY        2
`define FX3_WRITE_FULL_LATENCY    4

`define FX3_CHANGE_ADDR_LATENCY   3

//256
`define USB3_FIFO_DEPTH           8
//128
`define USB2_FIFO_DEPTH           7
`define USB3_MAX_COUNT            (2 ** (`USB3_FIFO_DEPTH))
`define USB2_MAX_COUNT            (2 ** (`USB2_FIFO_DEPTH))


`define FX3_INPUT_ADDR            0
`define FX3_OUTPUT_ADDR           1

module fx3_bus #(
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
output              o_gpif_clk,

inout       [31:0]  io_data,

output              o_cs_n,
output              o_oe_n,
output              o_we_n,
output              o_re_n,
output              o_pkt_end_n,

//DMA Flags
input               i_in_rdy,
input               i_out_rdy,

output  reg [1:0]   o_socket_addr,

output              o_gpif_int_n,


//Configuration
input               i_usb3_data_size_sel,

//Write side FIFO interface
output              o_ingress_ready,
input               i_ingress_activate,
output      [23:0]  o_ingress_packet_size,
output      [31:0]  o_ingress_data,
input               i_ingress_strobe,


//Read side FIFO interface
output      [1:0]   o_egress_ready,
input       [1:0]   i_egress_activate,
output      [23:0]  o_egress_size,
input       [31:0]  i_egress_data,
input               i_egress_strobe,

output      [7:0]   o_debug
);

//Local Parameters
localparam          IDLE              = 0;
localparam          READ_ADDR_SELECT  = 2;
localparam          READ_OUTPUT_EN    = 3;
localparam          READ_START        = 4;
localparam          READ              = 5;

localparam          WRITE_ADDR_SELECT = 6;
localparam          WRITE             = 7;

//Registers/Wires
reg                 chip_select;
reg                 output_enable;
reg                 read_enable;
reg                 write_enable;
reg                 packet_end;

reg         [31:0]  data_out;

reg         [3:0]   state;
reg         [3:0]   delay_count;

wire        [9:0]   data_count;
wire                busy;


wire        [31:0]  fx3_read_data;
wire        [1:0]   fx3_read_ready;
reg         [1:0]   fx3_read_activate;
wire        [23:0]  fx3_read_fifo_size;
reg                 fx3_read_strobe;
reg         [23:0]  read_count;


reg                 fx3_write_strobe;
wire                fx3_write_ready;
reg                 fx3_write_activate;
wire        [23:0]  fx3_fifo_size;
wire        [31:0]  fx3_write_data;
reg         [23:0]  write_count;

//Submodules
ppfifo #(
  .DATA_WIDTH       (32                   ),
  .ADDRESS_WIDTH    (`USB3_FIFO_DEPTH     )
)ingress_fifo(
  .reset            (rst                  ),

  //write side
  .write_clock     (clk                   ),
  .write_data      (fx3_read_data         ),
  .write_ready     (fx3_read_ready        ),
  .write_activate  (fx3_read_activate     ),
  .write_fifo_size (fx3_read_fifo_size    ),
  .write_strobe    (fx3_read_strobe       ),
  .starved         (                      ),

  //read side
  .read_clock      (clk                   ),
  .read_strobe     (i_ingress_strobe      ),
  .read_ready      (o_ingress_ready       ),
  .read_activate   (i_ingress_activate    ),
  .read_count      (o_ingress_packet_size ),
  .read_data       (o_ingress_data        ),
  .inactive        (                      )
);


ppfifo #(
  .DATA_WIDTH       (32                   ),
  .ADDRESS_WIDTH    (`USB3_FIFO_DEPTH     )
) egress_fifo (
  .reset            (rst                  ),

  //write side
  .write_clock      (clk                  ),
  .write_data       (i_egress_data       ),
  .write_ready      (o_egress_ready      ),
  .write_activate   (i_egress_activate   ),
//  .write_fifo_size  (o_egress_fifo_size  ),
  .write_strobe     (i_egress_strobe     ),
  .starved          (                     ),

  //read side
  .read_clock       (clk                  ),
  .read_strobe      (fx3_write_strobe     ),
  .read_ready       (fx3_write_ready      ),
  .read_activate    (fx3_write_activate   ),
  .read_count       (fx3_fifo_size        ),
  .read_data        (fx3_write_data       ),
  .inactive         (                     )

);

//Asynchronous Logic
assign  o_cs_n          = !chip_select;
assign  o_oe_n          = !output_enable;
assign  o_we_n          = !write_enable;
assign  o_re_n          = !read_enable;
assign  o_pkt_end_n     = !packet_end;

assign  fx3_read_data   = io_data;
assign  io_data         = output_enable ? 32'hZZZZZZZZ    : data_out;
assign  data_count      = i_usb3_data_size_sel       ? `USB3_MAX_COUNT : `USB2_MAX_COUNT;
assign  o_egress_size   = data_count;

assign  o_gpif_clk      = clk;
assign  o_gpif_int_n    = 1;

assign  busy            = (state != IDLE);

assign  o_debug         = {4'b0000,
                          fx3_write_activate,
                          busy,
                          i_out_rdy,
                          i_in_rdy};


//Synchronous Logic

always @ (posedge clk) begin
  write_enable          <=  0;
  packet_end            <=  0;
  fx3_read_strobe       <=  0;
  fx3_write_strobe      <=  0;

  if (rst) begin
    chip_select         <=  0;
    output_enable       <=  0;
    o_socket_addr       <=  0;
    data_out            <=  0;
    read_enable         <=  0;

    state               <=  IDLE;
    delay_count         <=  0;

    fx3_read_activate   <=  0;
    read_count          <=  0;

    fx3_write_activate  <=  0;

  end
  else begin
    //Get any available FIFO for reading data from the FX3 chip
    if ((fx3_read_ready > 0) && (fx3_read_activate == 0)) begin
      read_count              <=  0;
      if (fx3_read_ready[0]) begin
        fx3_read_activate[0]  <=  1;
      end
      else begin
        fx3_read_activate[1]  <=  1;
      end
    end

    //If there is any data available for writing to the host get it
    if (fx3_write_ready && !fx3_write_activate) begin
      write_count             <=  0;
      fx3_write_activate      <=  1;
    end

    if (delay_count > 0) begin
      delay_count <=  delay_count - 1;
    end
    else begin
      case (state)
        IDLE: begin
          o_socket_addr       <=  `FX3_INPUT_ADDR;
          output_enable       <=  0;
          chip_select         <=  0;
          read_enable         <=  0;
          //Determine if the master is ready to read data from FX3
          if (i_in_rdy && (fx3_read_activate > 0)) begin
            chip_select        <=  1;
            state             <=  READ_ADDR_SELECT;
          end
          else if (fx3_write_activate && i_out_rdy) begin    //MASTER WANTS TO SEND DATA TO FX3
            //XXX: IS THIS THE CORRECT SIGNAL???
            chip_select       <=  1;
            state             <=  WRITE_ADDR_SELECT;
          end
        end

        //Read State Machine
        READ_ADDR_SELECT: begin
          o_socket_addr       <=  `FX3_INPUT_ADDR;
          delay_count         <=  `FX3_CHANGE_ADDR_LATENCY;
          state               <=  READ_OUTPUT_EN;
        end
        READ_OUTPUT_EN: begin
          output_enable       <=  1;
          state               <=  READ_START;
        end
        READ_START: begin
          read_enable         <=  1;
          delay_count         <=  `FX3_READ_START_LATENCY;
          state               <=  READ;
        end
        READ: begin
          if ((read_count < data_count) && i_in_rdy) begin
            read_count        <=  read_count + 1;
            fx3_read_strobe   <=  1;
          end
          else begin
            fx3_read_activate <=  0;
            state             <=  IDLE;
            delay_count       <=  `FX3_READ_END_DELAY;
            chip_select       <=  0;
            output_enable     <=  0;
            read_enable       <=  0;
          end
        end

        //Write State Machine
        WRITE_ADDR_SELECT: begin
          o_socket_addr       <=  `FX3_OUTPUT_ADDR;
          delay_count         <=  `FX3_CHANGE_ADDR_LATENCY;
          state               <=  WRITE;
        end
        WRITE: begin
          if (write_count < fx3_fifo_size) begin
            write_enable      <=  1;
            if ((write_count == fx3_fifo_size - 1) && (fx3_fifo_size < data_count)) begin
              //we are at the last piece of data and it doesn't fill up the entire FIFO so we need to send a
              //packet end signal
              packet_end      <=  1;
            end
          end
          else begin
            state             <=  IDLE;
            delay_count       <=  `FX3_WRITE_FULL_LATENCY;
            chip_select       <=  0;
          end
        end
        default: begin
        end
      endcase
    end
  end
end
endmodule

