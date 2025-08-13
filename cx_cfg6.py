# cx_cfg.py

import ast
import sys
import os
import json
import networkx as nx
from typing import List, Optional, Any, Dict, Tuple

# --- 1. CFGNode Class Definition ---
class CFGNode:
    """Represents a basic block in the Control Flow Graph."""

    def __init__(self,
                 node_id: int,
                 ast_nodes: List[ast.stmt],
                 node_type: str = 'normal',
                 start_line: Optional[int] = None,
                 start_col: Optional[int] = None,
                 end_line: Optional[int] = None,
                 source_code: Optional[str] = None):
        self.node_id = node_id
        self.ast_nodes = ast_nodes
        self.start_line = start_line
        self.start_col = start_col
        self.end_line = end_line
        self.node_type = node_type
        self.source_code = source_code
        self.cfg_owner_node = None

    # return the statement # of a node, or its owner node statement #, or -1
    def getStartLine(self):
        if self.start_line is not None:
            return self.start_line
        elif self.cfg_owner_node:
            return self.cfg_owner_node.start_line
        else:
            return -1

    def to_dict(self) -> Dict[str, Any]:
        """Converts the CFGNode to a dictionary for serialization."""
        ast_node_reprs = []
        for node in self.ast_nodes:
            try:
                ast_node_reprs.append(ast.unparse(node))
            except AttributeError:
                ast_node_reprs.append(f"<{type(node).__name__} at L{node.lineno}C{node.col_offset}>")
            except Exception:
                ast_node_reprs.append(f"<Unparse Error for {type(node).__name__}>")

        if self.source_code is not None:
            display_source_code = self.source_code
        elif self.ast_nodes:
            display_source_code = "\n".join(ast_node_reprs)
        else:
            display_source_code = f"<{self.node_type}_node>"

        return {
            "node_id": self.node_id,
            "start_line": self.start_line if self.start_line is not None else -1,
            "start_col": self.start_col if self.start_col is not None else -1,
            "end_line": self.end_line if self.end_line is not None else -1,
            "node_type": self.node_type,
            "source_code": display_source_code,
            "ast_node_types": [type(n).__name__ for n in self.ast_nodes] if self.ast_nodes else []
        }

    def __repr__(self):
        line_info = f"lines={self.start_line}-{self.end_line}" if self.start_line is not None else "conceptual"
        return (f"CFGNode(id={self.node_id}, type='{self.node_type}', {line_info})")

# --- 2. CFGArc Class Definition ---
class CFGArc:
    """Represents a control flow transition (an edge) in the CFG."""

    def __init__(self,
                 source_id: int,
                 target_id: int,
                 arc_type: str,
                 condition: Optional[ast.expr] = None):
        self.source_id = source_id
        self.target_id = target_id
        self.arc_type = arc_type
        self.condition = condition

    def to_dict(self) -> Dict[str, Any]:
        """Converts the CFGArc to a dictionary for serialization."""
        condition_repr = None
        if self.condition:
            try:
                condition_repr = ast.unparse(self.condition)
            except AttributeError:
                condition_repr = f"<AST {type(self.condition).__name__} at L{getattr(self.condition, 'lineno', '?')}C{getattr(self.condition, 'col_offset', '?')}>"
            except Exception:
                condition_repr = f"<Unparse Error for {type(self.condition).__name__}>"

        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "arc_type": self.arc_type,
            "condition": condition_repr
        }

    def __repr__(self):
        cond_str = f", cond='{type(self.condition).__name__}'" if self.condition else ""
        return (f"CFGArc(from={self.source_id}, to={self.target_id}, "
                f"type='{self.arc_type}'{cond_str})")

# --- 3. CFG Class Definition ---
class CFG:
    """Represents a single Control Flow Graph for a function, method, or global scope."""

    def __init__(self, name: str, source_code_lines: List[str]):
        self.name = name
        self.source_code_lines = source_code_lines
        self._graph = nx.DiGraph()
        self._nodes_by_id: Dict[int, CFGNode] = {}
        self._next_node_id = 0

        self.entry_node_id: Optional[int] = None
        self.exit_node_id: Optional[int] = None

    def _get_next_node_id(self) -> int:
        """Internal helper to get a unique node ID."""
        node_id = self._next_node_id
        self._next_node_id += 1
        return node_id

    def add_node(self, ast_nodes: List[ast.stmt], node_type: str = 'normal', description: Optional[str] = None) -> CFGNode:
        """
        Creates a CFGNode object, adds it to the internal networkx graph,
        and stores the CFGNode object for lookup.
        Derives line numbers and source code from ast_nodes, or sets to None for conceptual nodes.
        """
        start_line: Optional[int] = None
        start_col: Optional[int] = None
        end_line: Optional[int] = None
        source_code_snippet: Optional[str] = None

        if ast_nodes:
            try:
                # Ensure all AST nodes have lineno/col_offset attributes
                start_line = ast_nodes[0].lineno
                start_col = ast_nodes[0].col_offset
                end_line = ast_nodes[-1].lineno
            except AttributeError:
                # This can happen for some non-statement AST nodes or synthetic ones
                pass # Keep as None, will be handled by CFGNode repr/to_dict

            if start_line is not None and end_line is not None:
                try:
                    # Adjust for 0-based indexing for source_code_lines
                    block_source_lines = self.source_code_lines[start_line - 1:end_line]
                    source_code_snippet = "\n".join(block_source_lines)
                except IndexError:
                    source_code_snippet = "<Source code not available>"
        else:
            # For conceptual nodes (entry, exit, join, etc.), description can be useful
            if description:
                source_code_snippet = f"<{node_type}_node: {description}>"
            else:
                source_code_snippet = f"<{node_type}_node>"

        node_id = self._get_next_node_id()
        cfg_node = CFGNode(
            node_id=node_id,
            ast_nodes=ast_nodes,
            start_line=start_line,
            start_col=start_col,
            end_line=end_line,
            node_type=node_type,
            source_code=source_code_snippet
        )
        self._graph.add_node(node_id, data=cfg_node)
        self._nodes_by_id[node_id] = cfg_node
        return cfg_node

    def add_arc(self, source_node: CFGNode, target_node: CFGNode, arc_type: str, condition: Optional[ast.expr] = None) -> CFGArc:
        """
        Creates a CFGArc object and adds an edge to the internal networkx graph.
        Takes CFGNode objects as source/target.
        """
        cfg_arc = CFGArc(
            source_id=source_node.node_id,
            target_id=target_node.node_id,
            arc_type=arc_type,
            condition=condition
        )
        self._graph.add_edge(source_node.node_id, target_node.node_id, data=cfg_arc)
        return cfg_arc

    def get_node(self, node_id: int) -> Optional[CFGNode]:
        """Retrieves the custom CFGNode object given its networkx ID."""
        return self._nodes_by_id.get(node_id)

    def get_successors(self, node_id: int) -> List[CFGNode]:
        """Returns a list of CFGNode objects that are direct successors of the given node."""
        successors = []
        for successor_id in self._graph.successors(node_id):
            node = self.get_node(successor_id)
            if node:
                successors.append(node)
        return successors

    def get_predecessors(self, node_id: int) -> List[CFGNode]:
        """Returns a list of CFGNode objects that are direct predecessors of the given node."""
        predecessors = []
        for predecessor_id in self._graph.predecessors(node_id):
            node = self.get_node(predecessor_id)
            if node:
                predecessors.append(node)
        return predecessors

    def get_arc(self, source_id, target_id):
        """
        Retrieve the CFGArc object between source and target IDs from the CFG's internal graph.
        """
        if self._graph.has_edge(source_id, target_id):
            data = self._graph.get_edge_data(source_id, target_id)
            if 'data' in data:
                return data['data']
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Serializes this single CFG (including its nodes and arcs) into a dictionary."""
        nodes_data = [node.to_dict() for node_id, node in self._nodes_by_id.items()]
        arcs_data = [self._graph.edges[u, v]['data'].to_dict() for u, v in self._graph.edges]

        return {
            "name": self.name,
            "entry_node_id": self.entry_node_id,
            "exit_node_id": self.exit_node_id,
            "nodes": nodes_data,
            "arcs": arcs_data
        }

    def _process_block(self,
                       statements: List[ast.stmt],
                       current_predecessors: List[CFGNode],
                       cfg_function_exit_node: CFGNode,
                       loop_context: List[Tuple[CFGNode, CFGNode]] # Added for break/continue targets (loop_exit, loop_continue)
                      ) -> List[CFGNode]:
        """
        Recursively processes a list of AST statements (a block), creating CFGNodes and arcs.
        Handles sequential statements and dispatches to specific handlers for control flow.

        Args:
            statements: The list of AST statements to process in this block.
            current_predecessors: A list of CFGNodes that are the immediate predecessors
                                  to the first statement in 'statements'.
            cfg_function_exit_node: The global exit node for the entire function/module CFG,
                                    used for 'return' statements.
            loop_context: A stack (list) of (loop_exit_node, loop_continue_node) for
                          handling break/continue in nested loops.

        Returns:
            A list of CFGNodes that represent the fallthrough points from this block.
            An empty list if the block always terminates (e.g., ends with 'return' or 'raise').
        """
        if not statements:
            # If the block is empty, its fallthroughs are simply its predecessors
            return current_predecessors

        # Nodes that are the current "last" nodes in the flow, ready to connect to the next statement
        active_fallthroughs: List[CFGNode] = list(current_predecessors)
        
        current_basic_block_stmts: List[ast.stmt] = []

        for i, stmt in enumerate(statements):
            # Check if the current statement is a control flow statement that
            # necessitates ending the current basic block and starting a new one.
            # Updated to include ast.Try and ast.With
            is_control_flow_or_terminator = isinstance(stmt, (
                ast.If, ast.For, ast.While, ast.Return, ast.Break, ast.Continue, ast.Raise, ast.With, ast.Try
            ))

            if is_control_flow_or_terminator:
                # If there are accumulated statements, create a 'normal' node for them first
                if current_basic_block_stmts:
                    normal_block_node = self.add_node(current_basic_block_stmts, node_type='normal')
                    for pred in active_fallthroughs:
                        self.add_arc(pred, normal_block_node, arc_type='fallthrough')
                    active_fallthroughs = [normal_block_node]
                    current_basic_block_stmts = [] # Reset for next block

                # Now handle the control flow statement itself
                if isinstance(stmt, ast.If):
                    if_join_nodes = self._handle_if_statement(stmt, active_fallthroughs, cfg_function_exit_node, loop_context)
                    active_fallthroughs = if_join_nodes # The join node becomes the predecessor for subsequent statements
                elif isinstance(stmt, ast.Return):
                    return_node = self.add_node([stmt], node_type='return')
                    for pred in active_fallthroughs:
                        self.add_arc(pred, return_node, arc_type='return')
                    self.add_arc(return_node, cfg_function_exit_node, arc_type='implicit_return_flow')
                    active_fallthroughs = [] # No fallthrough from a return statement
                    # Any subsequent statements in this block are unreachable
                    break
                elif isinstance(stmt, ast.While):
                    loop_fallthroughs = self._handle_while_loop(stmt, active_fallthroughs, cfg_function_exit_node, loop_context)
                    active_fallthroughs = loop_fallthroughs
                elif isinstance(stmt, ast.For):
                    loop_fallthroughs = self._handle_for_loop(stmt, active_fallthroughs, cfg_function_exit_node, loop_context)
                    active_fallthroughs = loop_fallthroughs
                elif isinstance(stmt, ast.Break):
                    break_node = self.add_node([stmt], node_type='break')
                    for pred in active_fallthroughs:
                        self.add_arc(pred, break_node, arc_type='fallthrough')
                    
                    if loop_context:
                        innermost_loop_exit, _ = loop_context[-1]
                        self.add_arc(break_node, innermost_loop_exit, arc_type='break_jump')
                    else:
                        # Break outside a loop, connect to function exit or mark as error
                        self.add_arc(break_node, cfg_function_exit_node, arc_type='error_break_no_loop')
                    
                    active_fallthroughs = [] # Break terminates flow from this path
                    break # No more statements in this block are reachable
                elif isinstance(stmt, ast.Continue):
                    continue_node = self.add_node([stmt], node_type='continue')
                    for pred in active_fallthroughs:
                        self.add_arc(pred, continue_node, arc_type='fallthrough')
                    
                    if loop_context:
                        _, innermost_loop_continue = loop_context[-1]
                        self.add_arc(continue_node, innermost_loop_continue, arc_type='continue_jump')
                    else:
                        # Continue outside a loop, connect to function exit or mark as error
                        self.add_arc(continue_node, cfg_function_exit_node, arc_type='error_continue_no_loop')
                    
                    active_fallthroughs = [] # Continue terminates flow from this path in current block
                    break # No more statements in this block are reachable
                elif isinstance(stmt, ast.Try):
                    try_fallthroughs = self._handle_try_statement(stmt, active_fallthroughs, cfg_function_exit_node, loop_context)
                    active_fallthroughs = try_fallthroughs
                elif isinstance(stmt, ast.With):
                    with_fallthroughs = self._handle_with_statement(stmt, active_fallthroughs, cfg_function_exit_node, loop_context)
                    active_fallthroughs = with_fallthroughs
                elif isinstance(stmt, ast.Raise):
                    # For now, raise acts as a terminator, similar to return.
                    # This will be refined in Phase 2 for exception paths.
                    raise_node = self.add_node([stmt], node_type='raise')
                    for pred in active_fallthroughs:
                        self.add_arc(pred, raise_node, arc_type='fallthrough')
                    self.add_arc(raise_node, cfg_function_exit_node, arc_type='implicit_raise_flow')
                    active_fallthroughs = [] # No fallthrough from a raise statement
                    break # Subsequent statements are unreachable

            else:
                # Accumulate sequential statements into the current basic block
                current_basic_block_stmts.append(stmt)
            
        # After loop, if there are remaining statements in current_basic_block_stmts,
        # create a final 'normal' node for them.
        if current_basic_block_stmts:
            final_normal_node = self.add_node(current_basic_block_stmts, node_type='normal')
            for pred in active_fallthroughs:
                self.add_arc(pred, final_normal_node, arc_type='fallthrough')
            active_fallthroughs = [final_normal_node]

        return active_fallthroughs


    def _handle_if_statement(self,
                             if_node: ast.If,
                             current_predecessors: List[CFGNode],
                             cfg_function_exit_node: CFGNode,
                             loop_context: List[Tuple[CFGNode, CFGNode]]) -> List[CFGNode]:
        """
        Handles an ast.If node, building its corresponding CFG structure:
        condition -> (true_branch_start / false_branch_start) -> join_node.

        Args:
            if_node: The AST If node.
            current_predecessors: CFGNodes that lead to this if statement.
            cfg_function_exit_node: The global exit node for the CFG, passed down for returns.
            loop_context: Current stack of loop targets for nested calls.

        Returns:
            A list containing the single CFGNode that is the join point
            after the if-else structure.
        """
        condition_node = self.add_node(
            [if_node.test], node_type='if_condition'
        )

        for pred in current_predecessors:
            self.add_arc(pred, condition_node, arc_type='normal')

        if_join_node = self.add_node([], node_type='if_join')

        # True branch
        true_branch_fallthroughs = self._process_block(if_node.body, [condition_node], cfg_function_exit_node, loop_context)
        for node in true_branch_fallthroughs:
            self.add_arc(node, if_join_node, arc_type='fallthrough')
        
        if if_node.body:
            first_true_body_node = None
            # Find the first node created by processing the true body.
            # This is a bit indirect, as _process_block creates nodes.
            # A more robust approach might have _process_block return its actual entry node if one is created.
            # For now, we assume the first node of the block's content is the first node generated.
            for succ_id in self._graph.successors(condition_node.node_id):
                succ_node = self.get_node(succ_id)
                if succ_node and succ_node.ast_nodes and succ_node.ast_nodes[0] == if_node.body[0]:
                    first_true_body_node = succ_node
                    break
            if first_true_body_node:
                self.add_arc(condition_node, first_true_body_node, arc_type='true_branch', condition=if_node.test)
            else: # Empty true body
                self.add_arc(condition_node, if_join_node, arc_type='true_branch', condition=if_node.test)
        else: # Empty true body
            self.add_arc(condition_node, if_join_node, arc_type='true_branch', condition=if_node.test)

        # False branch (else)
        if if_node.orelse:
            false_branch_fallthroughs = self._process_block(if_node.orelse, [condition_node], cfg_function_exit_node, loop_context)
            for node in false_branch_fallthroughs:
                self.add_arc(node, if_join_node, arc_type='fallthrough')
            
            if if_node.orelse:
                first_false_body_node = None
                for succ_id in self._graph.successors(condition_node.node_id):
                    succ_node = self.get_node(succ_id)
                    if succ_node and succ_node.ast_nodes and succ_node.ast_nodes[0] == if_node.orelse[0]:
                        first_false_body_node = succ_node
                        break
                
                if first_false_body_node:
                    self.add_arc(condition_node, first_false_body_node, arc_type='false_branch', condition=if_node.test)
                else: # Empty false body
                    self.add_arc(condition_node, if_join_node, arc_type='false_branch', condition=if_node.test)
            else: # Empty false body
                self.add_arc(condition_node, if_join_node, arc_type='false_branch', condition=if_node.test)
        else: # No else branch at all
            self.add_arc(condition_node, if_join_node, arc_type='false_branch', condition=if_node.test)

        return [if_join_node]


    def _handle_while_loop(self,
                           while_node: ast.While,
                           current_predecessors: List[CFGNode],
                           cfg_function_exit_node: CFGNode,
                           loop_context: List[Tuple[CFGNode, CFGNode]]) -> List[CFGNode]:
        """
        Handles an ast.While node, building its CFG structure:
        predecessors -> loop_condition -> loop_body -> loop_condition (back-edge)
                                        -> loop_exit (fallthrough from condition)

        Args:
            while_node: The AST While node.
            current_predecessors: CFGNodes that lead to this while loop.
            cfg_function_exit_node: The global exit node for the CFG.
            loop_context: Current stack of loop targets.

        Returns:
            A list containing the single CFGNode that is the exit point after the loop.
        """
        # 1. Create a node for the loop condition
        loop_condition_node = self.add_node([while_node.test], node_type='loop_condition')
        for pred in current_predecessors:
            self.add_arc(pred, loop_condition_node, arc_type='normal')

        # 2. Create a loop exit node
        loop_exit_node = self.add_node([], node_type='loop_exit')

        # 3. Add the loop_context for break/continue
        # loop_context[-1] should be (loop_exit_node, loop_continue_node)
        # For a while loop, continue jumps back to the condition node.
        new_loop_context = loop_context + [(loop_exit_node, loop_condition_node)]

        # 4. Process the loop body
        loop_body_fallthroughs = self._process_block(while_node.body, [loop_condition_node], cfg_function_exit_node, new_loop_context)

        # 5. Add back-edge from loop body fallthroughs to the condition node
        for node in loop_body_fallthroughs:
            self.add_arc(node, loop_condition_node, arc_type='loop_back')

        # 6. Add fallthrough from condition node to loop exit (when condition is false),
        #    BUT ONLY if there is no `else` block or if the `else` block is empty.
        #    If `else` exists, the false branch leads to the `else` block's entry.
        direct_to_exit_from_condition = True # Assume direct to exit unless else block handles it

        # 7. Handle `else` block for `while` (executed if loop finishes normally, without `break`)
        if while_node.orelse:
            # Create a separate block for the 'else' part of the while loop
            # This block is only entered if the loop condition becomes false *naturally*.
            while_else_fallthroughs = self._process_block(while_node.orelse, [loop_condition_node], cfg_function_exit_node, loop_context)
            
            # The 'else' block's fallthroughs also connect to the loop_exit_node
            for node in while_else_fallthroughs:
                self.add_arc(node, loop_exit_node, arc_type='fallthrough_from_else')
            
            # The false branch from the condition should go to the entry of the 'else' block
            first_else_body_node = None
            # Find the actual entry node of the else branch
            if while_node.orelse:
                # Need to find the first node generated by _process_block for while_node.orelse
                # This is a bit tricky, but it would be the first node whose predecessor is loop_condition_node
                # and whose AST content matches the first statement of orelse.
                for succ_id in self._graph.successors(loop_condition_node.node_id):
                    succ_node = self.get_node(succ_id)
                    if succ_node and succ_node.ast_nodes and succ_node.ast_nodes[0] == while_node.orelse[0]:
                        first_else_body_node = succ_node
                        break
            
            if first_else_body_node:
                self.add_arc(loop_condition_node, first_else_body_node, arc_type='false_branch_to_else', condition=while_node.test)
                direct_to_exit_from_condition = False # Handled by else branch

        if direct_to_exit_from_condition:
            self.add_arc(loop_condition_node, loop_exit_node, arc_type='false_branch', condition=while_node.test)

        return [loop_exit_node]


    def _handle_for_loop(self,
                          for_node: ast.For,
                          current_predecessors: List[CFGNode],
                          cfg_function_exit_node: CFGNode,
                          loop_context: List[Tuple[CFGNode, CFGNode]]) -> List[CFGNode]:
        """
        Handles an ast.For node, building its CFG structure:
        predecessors -> iterator_init -> loop_condition (get next) -> loop_body -> loop_condition (back-edge)
                                                                     -> loop_exit (no more items)

        Args:
            for_node: The AST For node.
            current_predecessors: CFGNodes that lead to this for loop.
            cfg_function_exit_node: The global exit node for the CFG.
            loop_context: Current stack of loop targets.

        Returns:
            A list containing the single CFGNode that is the exit point after the loop.
        """
        # 1. Create a node for iterator initialization/setup
        iterator_init_node = self.add_node([for_node.target, for_node.iter], node_type='iterator_init')
        for pred in current_predecessors:
            self.add_arc(pred, iterator_init_node, arc_type='normal')

        # 2. Create a loop condition node (implicitly "get next item" or "loop until done")
        loop_condition_node = self.add_node([], node_type='loop_condition_for',
                                            description=f"Iterate {ast.unparse(for_node.target)} in {ast.unparse(for_node.iter)}")
        # attach its source ownership
        loop_condition_node.cfg_owner_node = iterator_init_node
        # add arc to connect iterator_init -> loop_condition_for        
        self.add_arc(iterator_init_node, loop_condition_node, arc_type='normal')

        # 3. Create a loop exit node
        loop_exit_node = self.add_node([], node_type='loop_exit_for')

        # 4. Add the loop_context for break/continue
        new_loop_context = loop_context + [(loop_exit_node, loop_condition_node)]

        # 5. Process the loop body
        loop_body_fallthroughs = self._process_block(for_node.body, [loop_condition_node], cfg_function_exit_node, new_loop_context)

        # 6. Add back-edge from loop body fallthroughs to the condition node
        for node in loop_body_fallthroughs:
            self.add_arc(node, loop_condition_node, arc_type='loop_back')

        # 7. Add fallthrough from condition node to loop exit (when no more items),
        #    BUT ONLY if there is no `else` block or if the `else` block is empty.
        #    If `else` exists, this leads to the `else` block's entry.
        direct_to_exit_from_condition = True

        # 8. Handle `else` block for `for` (executed if loop finishes normally, without `break`)
        if for_node.orelse:
            for_else_fallthroughs = self._process_block(for_node.orelse, [loop_condition_node], cfg_function_exit_node, loop_context)
            for node in for_else_fallthroughs:
                self.add_arc(node, loop_exit_node, arc_type='fallthrough_from_else')
            
            # The 'no_more_items' from condition should specifically lead to the ELSE body entry if present
            first_else_body_node = None
            if for_node.orelse:
                for succ_id in self._graph.successors(loop_condition_node.node_id):
                    succ_node = self.get_node(succ_id)
                    if succ_node and succ_node.ast_nodes and succ_node.ast_nodes[0] == for_node.orelse[0]:
                        first_else_body_node = succ_node
                        break
            if first_else_body_node:
                self.add_arc(loop_condition_node, first_else_body_node, arc_type='no_more_items_to_else')
                direct_to_exit_from_condition = False

        if direct_to_exit_from_condition:
            self.add_arc(loop_condition_node, loop_exit_node, arc_type='no_more_items')

        return [loop_exit_node]


    def _handle_try_statement0(self,
                              try_node: ast.Try,
                              current_predecessors: List[CFGNode],
                              cfg_function_exit_node: CFGNode,
                              loop_context: List[Tuple[CFGNode, CFGNode]]) -> List[CFGNode]:
        """
        Handles an ast.Try node for Phase 1: Normal flow only.
        Models: predecessors -> try_body -> else_body -> finally_body -> try_join.
        Exception handlers (except blocks) are ignored in this phase.

        Args:
            try_node: The AST Try node.
            current_predecessors: CFGNodes that lead to this try statement.
            cfg_function_exit_node: The global exit node for the CFG.
            loop_context: Current stack of loop targets.

        Returns:
            A list containing the single CFGNode that is the join point
            after the try-except-else-finally structure for normal flow.
        """
        try_entry_node = self.add_node([], node_type='try_entry')
        for pred in current_predecessors:
            self.add_arc(pred, try_entry_node, arc_type='normal')

        # Fallthroughs from current block to the next
        current_block_fallthroughs = [try_entry_node]

        # 1. Process the `try` block
        try_body_fallthroughs = self._process_block(try_node.body, current_block_fallthroughs, cfg_function_exit_node, loop_context)
        current_block_fallthroughs = try_body_fallthroughs

        # 2. Process the `else` block (if no exception occurred in try block)
        # In Phase 1, we assume the 'normal' path, so 'else' follows 'try'.
        if try_node.orelse:
            else_body_fallthroughs = self._process_block(try_node.orelse, current_block_fallthroughs, cfg_function_exit_node, loop_context)
            current_block_fallthroughs = else_body_fallthroughs
        
        # 3. Process the `finally` block (always executes)
        # In Phase 1, it executes after the 'normal' flow of try/else.
        if try_node.finalbody:
            finally_body_fallthroughs = self._process_block(try_node.finalbody, current_block_fallthroughs, cfg_function_exit_node, loop_context)
            current_block_fallthroughs = finally_body_fallthroughs
        
        # 4. Create a join node for the entire try-except-else-finally structure
        try_join_node = self.add_node([], node_type='try_join')
        for node in current_block_fallthroughs:
            self.add_arc(node, try_join_node, arc_type='fallthrough')
        
        # Phase 1: Exception handlers (try_node.handlers) are ignored.

        return [try_join_node]

    def _handle_try_statement(self,
                              try_node: ast.Try,
                              current_predecessors: List[CFGNode],
                              cfg_function_exit_node: CFGNode,
                              loop_context: List[Tuple[CFGNode, CFGNode]]) -> List[CFGNode]:
        """
        Handles an ast.Try node, building its full CFG structure including
        try, except, else, and finally blocks.

        Control flow:
        - predecessors -> try_entry
        - try_entry (normal) -> try_body_start
        - try_body_fallthroughs -> (else_body_start OR finally_entry OR try_join)
        - try_entry (exception_jump) -> each except_handler_entry
        - each except_handler_body_fallthroughs -> (finally_entry OR try_join)
        - else_body_fallthroughs -> (finally_entry OR try_join)
        - finally_entry -> finally_body_start (if finalbody exists)
        - finally_body_fallthroughs -> try_join (if finalbody exists)
        - All paths eventually lead to try_join.

        Args:
            try_node: The AST Try node.
            current_predecessors: CFGNodes that lead to this try statement.
            cfg_function_exit_node: The global exit node for the CFG, passed down for returns.
            loop_context: Current stack of loop targets for nested calls.

        Returns:
            A list containing the single CFGNode that is the common join point
            after the entire try-except-else-finally structure.
        """
        # Create an entry node for the entire try block structure
        try_entry_node = self.add_node([], node_type='try_entry')
        for pred in current_predecessors:
            self.add_arc(pred, try_entry_node, arc_type='normal')

        # List to collect all fallthroughs from try, except, and else bodies
        # These will eventually lead to the finally block or the try_join node
        paths_to_finally_or_join: List[CFGNode] = []

        # ----------------------------------------
        # 1. Process the `try` block
        # ----------------------------------------
        # _process_block returns the fallthrough nodes from the try body
        # (i.e., paths that completed without an immediate return, break, continue, or raise)
        try_body_fallthroughs = self._process_block(
            try_node.body,
            [try_entry_node], # Try body starts after try_entry_node
            cfg_function_exit_node,
            loop_context
        )
        paths_to_finally_or_join.extend(try_body_fallthroughs)

        # ----------------------------------------
        # 2. Process `except` blocks
        # ----------------------------------------
        for handler in try_node.handlers:
            # Create an entry node for each specific except handler
            except_type_str = ast.unparse(handler.type) if handler.type else "AnyException"
            except_description = f"except {except_type_str}"
            if handler.name:
                except_description += f" as {ast.unparse(handler.name)}"
            
            except_entry_node = self.add_node(
                [handler.type] if handler.type else [], # Use the exception type AST node for source
                node_type='except_handler_entry',
                description=except_description
            )
            
            # Add an arc from the try_entry_node to this except handler.
            # This models an exception being raised within the try block and jumping here.
            # For a more advanced CFG, these arcs would originate from specific statements
            # in the try block that can raise exceptions. For now, a general jump.
            self.add_arc(try_entry_node, except_entry_node, arc_type='exception_jump', condition=handler.type)
            
            # Process the body of the current except handler
            except_body_fallthroughs = self._process_block(
                handler.body,
                [except_entry_node], # Except body starts after its entry node
                cfg_function_exit_node,
                loop_context
            )
            paths_to_finally_or_join.extend(except_body_fallthroughs)

        # ----------------------------------------
        # 3. Process the `else` block
        # ----------------------------------------
        # The 'else' block only executes if the 'try' block completes without an exception.
        # So its predecessors are the fallthroughs from the try body that didn't raise.
        if try_node.orelse:
            # Ensure there were paths from the try body to connect to the else
            if try_body_fallthroughs: # Only proceed if try block had normal fallthroughs
                else_body_fallthroughs = self._process_block(
                    try_node.orelse,
                    try_body_fallthroughs, # Else block follows successful try execution
                    cfg_function_exit_node,
                    loop_context
                )
                # Remove fallthroughs from try_body that now go to else_body
                for node in try_body_fallthroughs:
                    if node in paths_to_finally_or_join:
                        paths_to_finally_or_join.remove(node)
                paths_to_finally_or_join.extend(else_body_fallthroughs)
            else:
                # If try body had no fallthroughs (e.g., always returns/raises), else is unreachable
                print(f"Warning: 'else' block for try statement at L{try_node.lineno} is unreachable in normal flow.")
        
        # ----------------------------------------
        # 4. Handle the `finally` block
        # ----------------------------------------
        final_block_exit_points: List[CFGNode] = []
        if try_node.finalbody:
            # Create an entry node for the finally block
            finally_entry_node = self.add_node([], node_type='finally_entry')
            
            # All paths from try, except, and else (that haven't terminated)
            # must lead to the finally block.
            for node in paths_to_finally_or_join:
                self.add_arc(node, finally_entry_node, arc_type='to_finally')
            
            # Process the finally body
            final_block_exit_points = self._process_block(
                try_node.finalbody,
                [finally_entry_node], # Finally body starts after its entry node
                cfg_function_exit_node,
                loop_context
            )
        else:
            # If no finally block, the fallthroughs collected so far are the final ones
            final_block_exit_points = paths_to_finally_or_join
        
        # ----------------------------------------
        # 5. Create a join node for the entire structure
        # ----------------------------------------
        try_join_node = self.add_node([], node_type='try_join')
        
        # Connect all final exit points from the try-except-else-finally structure to the join node
        for node in final_block_exit_points:
            self.add_arc(node, try_join_node, arc_type='fallthrough')
        
        return [try_join_node]


    def _handle_with_statement(self,
                               with_node: ast.With,
                               current_predecessors: List[CFGNode],
                               cfg_function_exit_node: CFGNode,
                               loop_context: List[Tuple[CFGNode, CFGNode]]) -> List[CFGNode]:
        """
        Handles an ast.With node for Phase 1: Normal flow only.
        Models: predecessors -> with_entry -> with_body -> with_exit -> fallthrough.
        Implicit exception handling/propagation from context manager is ignored in this phase.

        Args:
            with_node: The AST With node.
            current_predecessors: CFGNodes that lead to this with statement.
            cfg_function_exit_node: The global exit node for the CFG.
            loop_context: Current stack of loop targets.

        Returns:
            A list containing the single CFGNode that is the exit point after the with statement.
        """
        # 1. Create a node for the context manager entry
        # This represents `with ... as ...:` setup
        with_entry_node = self.add_node([assign.value for assign in with_node.items] if with_node.items else [],
                                        node_type='with_entry',
                                        description=f"Enter context: {ast.unparse(with_node)}")
        for pred in current_predecessors:
            self.add_arc(pred, with_entry_node, arc_type='normal')
        
        # 2. Process the `with` block body
        with_body_fallthroughs = self._process_block(with_node.body, [with_entry_node], cfg_function_exit_node, loop_context)

        # 3. Create a node for the context manager exit
        # This represents the `__exit__` call and cleanup
        with_exit_node = self.add_node([], node_type='with_exit',
                                       description=f"Exit context: {ast.unparse(with_node)}")
        
        for node in with_body_fallthroughs:
            self.add_arc(node, with_exit_node, arc_type='fallthrough')
        
        # Phase 1: Implicit exception handling during context exit is ignored.

        return [with_exit_node]


    def _build_graph_from_ast(self, ast_subtree: ast.AST) -> None:
        """
        (CORE IMPLEMENTATION)
        Constructs the CFG for the given AST subtree (e.g., function body, module body).
        This method sets up entry/exit nodes and then delegates to _process_block.
        """
        #print(f"  Building CFG for '{self.name}' from AST.")

        entry_node = self.add_node([], node_type='entry')
        self.entry_node_id = entry_node.node_id

        exit_node = self.add_node([], node_type='exit_point')
        self.exit_node_id = exit_node.node_id

        statements_to_process: List[ast.stmt] = []
        if isinstance(ast_subtree, ast.Module):
            statements_to_process = ast_subtree.body
        elif isinstance(ast_subtree, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            statements_to_process = ast_subtree.body
        else:
            raise ValueError(f"Unsupported AST subtree type for CFG building: {type(ast_subtree).__name__}")

        # Initial call to _process_block with an empty loop_context
        final_fallthroughs_from_main_block = self._process_block(
            statements_to_process,
            [entry_node],
            exit_node,
            [] # Start with an empty loop_context
        )

        for node in final_fallthroughs_from_main_block:
            if node.node_id != exit_node.node_id and not self._graph.has_edge(node.node_id, exit_node.node_id):
                self.add_arc(node, exit_node, arc_type='fallthrough_to_cfg_exit')

# --- 4. CFGManager Class Definition ---
class CFGManager:
    """Manages the creation and storage of multiple CFGs for a given source file."""

    def __init__(self):
        self.cfgs: Dict[str, CFG] = {}
        self.source_code: Optional[str] = None
        self.source_code_lines: List[str] = []

    def load_from_file(self, filename: str) -> None:
        """
        Loads source code from file, parses it, and builds CFGs for all
        functions/methods/global scope.
        """
        if not os.path.exists(filename):
            raise FileNotFoundError(f"File not found: {filename}")

        with open(filename, 'r', encoding='utf-8') as f:
            self.source_code = f.read()

        self.load_from_string(self.source_code, filename)

    def load_from_string(self, source_code, filename='') -> None:
        """
        Using source code from string, parses it, and builds CFGs for all
        functions/methods/global scope.
        """
        module_ast = ast.parse(source_code, filename=filename)
        self.load_from_ast(module_ast, source_code, filename)

    def load_from_ast(self, module_ast, source_code, filename=None) -> None:
        """
        Loads ast tree and source code, and builds CFGs for all
        functions/methods/global scope.
        """
        #if not os.path.exists(filename):
        #    raise FileNotFoundError(f"File not found: {filename}")

        #with open(filename, 'r', encoding='utf-8') as f:
        #    self.source_code = f.read()
        self.source_code = source_code
        self.source_code_lines = source_code.splitlines()

        #print(f"Processing '{filename}' to build CFGs...")

        #module_ast = ast.parse(self.source_code, filename=filename)
        self.module_ast = module_ast

        # --- 4.1. Build CFG for the Global Scope ---
        #global_cfg_name = f"__global__({os.path.basename(filename)})" if filename else "__global__(in_memory)"
        global_cfg_name = '<global>'
        global_cfg = CFG(name=global_cfg_name, source_code_lines=self.source_code_lines)
        
        global_statements: List[ast.stmt] = []
        
        for stmt in module_ast.body:
            if not isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                global_statements.append(stmt)
        
        class _MockGlobalModule(ast.Module):
            def __init__(self, body_stmts):
                self.body = body_stmts
                self.lineno = 1
                self.col_offset = 0
                self.type_ignores = []

        global_cfg._build_graph_from_ast(_MockGlobalModule(global_statements))
        self.cfgs[global_cfg_name] = global_cfg


        # --- 4.2. Build CFGs for Functions and Methods ---
        for stmt in module_ast.body:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_name = stmt.name
                func_cfg = CFG(name=func_name, source_code_lines=self.source_code_lines)
                func_cfg._build_graph_from_ast(stmt)
                self.cfgs[func_name] = func_cfg
            elif isinstance(stmt, ast.ClassDef):
                for class_stmt in stmt.body:
                    if isinstance(class_stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        method_name = f"{stmt.name}.{class_stmt.name}"
                        method_cfg = CFG(name=method_name, source_code_lines=self.source_code_lines)
                        method_cfg._build_graph_from_ast(class_stmt)
                        self.cfgs[method_name] = method_cfg

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the manager's state, including all contained CFGs."""
        return {name: cfg.to_dict() for name, cfg in self.cfgs.items()}

    def get_all_cfgs(self) -> Dict[str, CFG]:
        """Returns all built CFG objects."""
        return self.cfgs


# --- 5. Example Test Code for if __name__ == '__main__': (Updated) ---
if __name__ == '__main__':
    print("--- Testing cx_cfg.py components ---")

    class MockASTNode(ast.stmt):
        def __init__(self, lineno, col_offset, value):
            self.lineno = lineno
            self.col_offset = col_offset
            self.value = value
        def __repr__(self):
            return f"MockASTNode(L{self.lineno}C{self.col_offset}, '{self.value}')"

    if not hasattr(ast, 'unparse'):
        # Polyfill for ast.unparse for older Python versions, if needed
        def mock_unparse(node):
            if isinstance(node, MockASTNode): return f"mock_code: {node.value}"
            if isinstance(node, ast.expr) and hasattr(node, 'lineno'): return f"<EXPR at L{node.lineno}>"
            if isinstance(node, ast.stmt) and hasattr(node, 'lineno'): return f"<STMT at L{node.lineno}>"
            return str(node)
        ast.unparse = mock_unparse
        print("Using mock ast.unparse for compatibility.")


    # --------------------------------------------------------------------------
    # Demo of CFGNode instantiation and to_dict()
    # --------------------------------------------------------------------------
    print("\n--- CFGNode Demo ---")
    mock_ast_node_1 = MockASTNode(lineno=10, col_offset=4, value="x = 1")
    mock_ast_node_2 = MockASTNode(lineno=11, col_offset=4, value="print(x)")

    test_node = CFGNode(
        node_id=0,
        ast_nodes=[mock_ast_node_1, mock_ast_node_2],
        start_line=10,
        start_col=4,
        end_line=11,
        node_type='entry',
        source_code="x = 1\nprint(x)"
    )

    print(f"CFGNode __repr__: {test_node!r}")
    print("\nCFGNode.to_dict() output:")
    print(json.dumps(test_node.to_dict(), indent=2))


    # --------------------------------------------------------------------------
    # Demo of CFGManager and CFG loading with actual AST parsing
    # Now includes 'if', 'while', 'for', 'break', 'continue', 'try', 'with'
    # --------------------------------------------------------------------------
    print("\n--- Full CFG Building Demo ---")
    print("This section now handles 'if', 'while', 'for', 'break', 'continue', 'try' (normal flow), and 'with' (normal flow) statements.")

    if len(sys.argv) < 2:
        print("\nSkipping full CFG building demo: No input file provided. Run with 'python cx_cfg.py <path_to_python_file>'.")
        # Create a dummy file for testing if no argument is provided
        dummy_file_content = """
# example_test_cfg.py
x = 10
if x > 5:
    print("x is large")
    y = 20
elif x == 10:
    print("x is ten")
else:
    print("x is small")
    y = 5
z = y + 1

i = 0
while i < 3:
    print(f"While loop iteration {i}")
    i += 1
    if i == 2:
        break # Exits the while loop
else:
    print("While loop finished normally") # Should not print if break
print("After while loop")

for item in [1, 2, 3]:
    if item == 2:
        continue # Skips print for 2
    print(f"For loop item: {item}")
else:
    print("For loop finished normally")
print("After for loop")

try:
    print("Inside try block")
    value = 1 / 1 # No error
except ZeroDivisionError:
    print("Caught ZeroDivisionError") # This path ignored in Phase 1
except Exception as e:
    print(f"Caught other exception: {e}") # This path ignored in Phase 1
else:
    print("Try block completed without error (else block)")
finally:
    print("Finally block always executes")
print("After try-except-else-finally")

with open("test.txt", "w") as f:
    f.write("Hello, world!")
print("After with statement")

def my_function(a):
    if a % 2 == 0:
        return "Even"
    else:
        return "Odd"
    print("This is unreachable") # Should be unreachable due to return
final_result = my_function(z)
"""
        dummy_filename = "example_test_cfg.py"
        with open(dummy_filename, "w") as f:
            f.write(dummy_file_content)
        print(f"Created a dummy test file: {dummy_filename}. Running CFG generation on it.")
        input_filename = dummy_filename
    else:
        input_filename = sys.argv[1]
    
    if not os.path.exists(input_filename):
        print(f"\nSkipping full CFG building demo: File not found at '{input_filename}'.")
        sys.exit(0)

    print(f"\nAttempting to load and export CFGs from '{input_filename}'...")

    manager = CFGManager()
    try:
        manager.load_from_file(input_filename)
        print("\n--- CFGManager to_dict() output (Full JSON) ---")
        # For readability, let's print a summary rather than the full JSON which can be large
        # print(json.dumps(manager.to_dict(), indent=2))

        # Instead, let's print a more digestible summary for each CFG
        for cfg_name, cfg_obj in manager.get_all_cfgs().items():
            print(f"\n--- CFG: {cfg_name} ---")
            print(f"  Entry Node ID: {cfg_obj.entry_node_id}")
            print(f"  Exit Node ID: {cfg_obj.exit_node_id}")
            print(f"  Total Nodes: {len(cfg_obj._nodes_by_id)}")
            print(f"  Total Arcs: {len(cfg_obj._graph.edges)}")
            print("  Nodes (ID, Type, Lines, Source Snippet):")
            for node_id, node in cfg_obj._nodes_by_id.items():
                source_preview = (node.source_code.splitlines()[0][:50] + "..." if node.source_code and len(node.source_code) > 50 else node.source_code) if node.source_code else ""
                print(f"    - {node.node_id}: {node.node_type} (L{node.start_line or '?'}-L{node.end_line or '?'}) - '{source_preview}'")
            print("  Arcs (Source -> Target, Type, Condition):")
            for u, v, data in cfg_obj._graph.edges(data=True):
                arc = data['data']
                cond_str = f" (cond: '{arc.condition}')" if arc.condition else ""
                print(f"    - {arc.source_id} -> {arc.target_id} [{arc.arc_type}]{cond_str}")


    except Exception as e:
        print(f"An error occurred during CFG loading/building: {e}")
        import traceback; traceback.print_exc()
        print("\nReview the traceback above to debug issues with AST parsing or CFG construction.")

    print("\n--- End of cx_cfg.py execution ---")