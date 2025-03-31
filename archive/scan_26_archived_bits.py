import pyslang


def extract_list_of_logics_bad(ast: pyslang.SyntaxTree) -> list[str]:
    """Read all logic from a file and return a list of logic objects."""
    
    identifiers: dict[str, list[str]] = {}
    
    def handle(node: pyslang.SyntaxNode | pyslang.Token) -> None:
        assert isinstance(node, pyslang.SyntaxNode | pyslang.Token)
        
        print(f"node - {repr(node)} - type={type(node)}: \n\n{node}\n\n")
        
        if node.kind == pyslang.SyntaxKind.DataDeclaration:
            this_list_type = None

            for subnode in node:
                assert isinstance(subnode, pyslang.SyntaxNode | pyslang.Token)
                print(f"subnode - {repr(subnode)} - type={type(subnode)}: \n\n{subnode}\n\n")

                # First, figure out what type of list we are dealing with.
                if subnode.kind == pyslang.SyntaxKind.LogicType:
                    this_list_type = "logic"
                    continue
                elif subnode.kind == pyslang.SyntaxKind.RegType:
                    this_list_type = "reg"
                    continue

                if subnode.kind == pyslang.SyntaxKind.SeparatedList:
                    for subsubnode in subnode:
                        assert isinstance(subsubnode, pyslang.SyntaxNode | pyslang.Token)
                        if isinstance(subsubnode, pyslang.Token):
                            if this_list_type is None:
                                raise ValueError("No list type found for identifier.")
                            if this_list_type not in identifiers:
                                identifiers[this_list_type] = []
                            identifiers[this_list_type].append(str(subsubnode))

                1
                1

                # if isinstance(subnode, pyslang.Token):
                #     if this_list_type is None:
                #         raise ValueError("No list type found for identifier.")
                #     if this_list_type not in identifiers:
                #         identifiers[this_list_type] = []
                #     identifiers[this_list_type].append(str(subnode))



    assert isinstance(ast.root, pyslang.SyntaxNode)
    ast.root.visit(handle)
    
    return identifiers.get("logic", [])


def extract_list_of_logics(tree: pyslang.SyntaxTree) -> list[str]:
    # Step 1: Set up the source manager and syntax tree
    # source_manager = pyslang.SourceManager()
    # tree = pyslang.SyntaxTree.fromText(verilog) # , source_manager)

    # Step 2: Compile the syntax tree
    compilation = pyslang.Compilation()
    compilation.addSyntaxTree(tree)

    # Step 3: Get the root symbol for the top-level module
    top = compilation.getRoot().topInstances[0] # [0]# .definition

    # Step 4: Traverse members to find 'logic' variables
    logic_names = []
    for member in top:
        if isinstance(member, pyslang.VariableSymbol):
            type_str = member.declaredType.getType().toString()
            if "logic" in type_str:
                logic_names.append(member.name)

    return logic_names

