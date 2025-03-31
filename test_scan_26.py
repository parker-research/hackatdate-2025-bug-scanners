# import pyslang

from scan_26_single_const_assign import (
    extract_declared_identifiers,
    count_constant_assignments_to_identifier,
    find_all_single_constant_assignments_in_verilog,
)


def test_always_true() -> None:
    assert True


def test_extract_declared_identifiers() -> None:
    verilog = """
module memory(
    address,
    data_in,
    data_out,
    read_write,
    chip_en
);

    input wire [7:0] address, data_in;
    output reg [7:0] data_out;
    input wire read_write, chip_en;
    logic i_am_a_logic;
    logic i_am_a_logic_array [0:255];

    reg [7:0] mem [0:255];

    always @ (address or data_in or read_write or chip_en)
        if (read_write == 1 && chip_en == 1) begin
            mem[address] = data_in;
        end

    always @ (read_write or chip_en or address)
        if (read_write == 0 && chip_en)
            data_out = mem[address];
        else
            data_out = 0;

endmodule
        """

    result = extract_declared_identifiers(verilog)
    assert result["input wire"] == ["address", "data_in", "read_write", "chip_en"]
    assert result["output reg"] == ["data_out"]
    assert result["logic"] == ["i_am_a_logic", "i_am_a_logic_array"]
    assert result["reg"] == ["mem"]
    assert len(result) == 4


VERILOG_SAMPLE_1 = """
module ConvolutedLogic (
    input  wire clk,
    input  wire rst,
    input  wire [3:0] selector,
    output wire result
);

    // The one-time assigned constant wire
    wire only_written_to_once_as_const;
    assign only_written_to_once_as_const = 1'b1;

    // Internal wires to demonstrate convoluted usage
    wire inverted;
    wire mux_out;
    wire and_tree;
    wire weird_xor;
    wire [3:0] replicated_bits;
    wire feedback;

    // 1. Inversion usage
    assign inverted = ~only_written_to_once_as_const;

    // 2. Mux-style usage
    assign mux_out = (selector[0]) ? only_written_to_once_as_const : inverted;

    // 3. AND-tree logic (with other signals)
    assign and_tree = only_written_to_once_as_const &
                      selector[1] &
                      (only_written_to_once_as_const | selector[2]);

    // 4. XOR madness
    assign weird_xor = only_written_to_once_as_const ^ 
                       selector[3] ^ 
                       (inverted & only_written_to_once_as_const);

    // 5. Replication and reduction
    assign replicated_bits = {4{only_written_to_once_as_const}};
    wire reduction_and = &replicated_bits;

    // 6. Feedback-like illusion (not really feedback but looks like it)
    reg dummy_register;
    always @(posedge clk or posedge rst) begin
        if (rst)
            dummy_register <= 1'b0;
        else
            dummy_register <= (only_written_to_once_as_const & selector[2]) ^ mux_out;
    end

    assign feedback = dummy_register & only_written_to_once_as_const;

    // Final output: wrap it all together
    assign result = (mux_out | weird_xor) & and_tree & feedback & reduction_and;

endmodule
    """


def test_count_constant_assignments_to_identifier_1() -> None:
    assert 1 == count_constant_assignments_to_identifier(
        VERILOG_SAMPLE_1, "only_written_to_once_as_const"
    )
    assert 0 == count_constant_assignments_to_identifier(
        VERILOG_SAMPLE_1, "dummy_register"
    )
    assert 0 == count_constant_assignments_to_identifier(VERILOG_SAMPLE_1, "inverted")
    assert 0 == count_constant_assignments_to_identifier(VERILOG_SAMPLE_1, "mux_out")
    assert 0 == count_constant_assignments_to_identifier(VERILOG_SAMPLE_1, "and_tree")
    assert 0 == count_constant_assignments_to_identifier(VERILOG_SAMPLE_1, "weird_xor")
    assert 0 == count_constant_assignments_to_identifier(
        VERILOG_SAMPLE_1, "replicated_bits"
    )
    assert 0 == count_constant_assignments_to_identifier(
        VERILOG_SAMPLE_1, "reduction_and"
    )
    assert 0 == count_constant_assignments_to_identifier(VERILOG_SAMPLE_1, "feedback")
    assert 0 == count_constant_assignments_to_identifier(VERILOG_SAMPLE_1, "result")
    assert 0 == count_constant_assignments_to_identifier(
        VERILOG_SAMPLE_1, "not_an_identifier"
    )


def test_find_all_single_constant_assignments_in_verilog() -> None:
    result = find_all_single_constant_assignments_in_verilog(VERILOG_SAMPLE_1)
    assert len(result) == 1
    assert result[0] == ("only_written_to_once_as_const", "wire")
