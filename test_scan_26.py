# import pyslang

from scan_26_single_const_assign import extract_declared_identifiers


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


if __name__ == "__main__":
    test_always_true()
    