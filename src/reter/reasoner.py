"""
Description Logic Reasoner using C++ OWL RETE with C++ DL Parser
Simplified reasoner that uses C++ parser directly - NO Python Lark dependency!
"""

import os
import sys

# Import pyarrow first to ensure Arrow DLLs are available (required for Arrow integration on Windows)
try:
    import pyarrow
except ImportError:
    pass  # Arrow support optional

# Import C++ RETE implementation from reter_core
# The C++ extension module is now in the separate reter_core package
try:
    from reter_core import owl_rete_cpp
except ImportError as e:
    raise ImportError(
        "Failed to import owl_rete_cpp from reter_core package. "
        "Please ensure reter_core is installed: pip install reter_core"
    ) from e


class QueryResultSet:
    """
    Wrapper around a query production's results
    Provides iteration, indexing, and conversion to pandas

    Week 6 Extensions:
    - Indexed access: results[0], results[-1]
    - Slicing: results[5:10], results[:100]
    - Efficient caching of materialized results

    @reter-cnl: This is-in-layer Core-Layer.
    @reter-cnl: This is a data-transfer-object.
    """

    def __init__(self, production, variables, network, tokens=None):
        """
        Args:
            production: ProductionNode from build_query_pattern
            variables: List of variable names (e.g., ["?x", "?age"])
            network: ReteNetwork instance
            tokens: Optional pre-fetched token vector (for template queries)
        """
        self._production = production
        self._variables = variables
        self._network = network
        self._arrow_table = None  # For Week 2
        self._tokens = tokens  # NEW: Cache for template queries (Week 3)

    def __iter__(self):
        """Iterate over result bindings (zero-copy)"""
        # Use cached tokens if available (template queries), otherwise fetch from production
        if self._tokens is not None:
            tokens = self._tokens
        else:
            tokens = self._network.get_query_results(self._production)

        for token in tokens:
            # Use extract_bindings to get variable bindings from token using production's binding extractor
            bindings = self._network.extract_bindings(self._production, token)
            # Return only requested variables
            if self._variables:
                yield {v: bindings.get(v, None) for v in self._variables}
            else:
                yield bindings

    def __len__(self):
        """Number of results"""
        # Use cached tokens if available (template queries), otherwise fetch from production
        if self._tokens is not None:
            return len(self._tokens)
        else:
            tokens = self._network.get_query_results(self._production)
            return len(tokens)

    def __getitem__(self, key):
        """
        Support indexed access and slicing (Week 6 - C++ optimized)

        Examples:
            results[0]       # First result
            results[-1]      # Last result
            results[5:10]    # Slice of results
            results[:100]    # First 100 results

        Returns:
            Single dict (for int index) or list of dicts (for slice)
        """
        # Handle integer indexing - direct C++ call, no materialization
        if isinstance(key, int):
            try:
                token = self._network.get_query_result_at_index(self._production, key)
                bindings = self._network.extract_bindings(self._production, token)
                if self._variables:
                    return {v: bindings.get(v, None) for v in self._variables}
                else:
                    return bindings
            except Exception as e:
                # Handle out of range errors
                raise IndexError(str(e))

        # Handle slicing - use C++ slice method for efficiency
        elif isinstance(key, slice):
            # Calculate slice indices
            start, stop, step = key.start, key.stop, key.step

            # Default values
            if start is None:
                start = 0
            if step is None:
                step = 1
            if stop is None:
                # Get count without fetching all results
                stop = self._network.get_query_result_count(self._production)

            # Get slice from C++
            tokens = self._network.get_query_results_slice(self._production, start, stop, step)

            # Extract bindings from each token
            results = []
            for token in tokens:
                bindings = self._network.extract_bindings(self._production, token)
                if self._variables:
                    results.append({v: bindings.get(v, None) for v in self._variables})
                else:
                    results.append(bindings)

            return results
        else:
            raise TypeError(f"Indices must be integers or slices, not {type(key).__name__}")

    def __repr__(self):
        return f"QueryResultSet({len(self)} results, variables={self._variables})"

    def to_list(self):
        """Convert to list of dicts"""
        return list(self)

    def to_pandas(self):
        """
        Convert query results to pandas DataFrame using zero-copy Arrow conversion

        Returns:
            pandas.DataFrame with one column per variable

        Example:
            results = r.pattern(("?x", "type", "Person"), ("?x", "hasAge", "?age"))
            df = results.to_pandas()
            print(df.head())
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas is required for to_pandas(). Install with: pip install pandas")

        try:
            import pyarrow
            ARROW_AVAILABLE = True
        except ImportError:
            ARROW_AVAILABLE = False

        # Try Arrow conversion first (zero-copy, fast)
        if ARROW_AVAILABLE and hasattr(self._network, 'tokens_to_arrow'):
            try:
                # IMPORTANT: Cannot cache Arrow table on Python side!
                # The RETE network has live updates - tokens are added/removed
                # as facts change. We must rebuild the Arrow table on each call
                # to get current results.
                arrow_table = self._network.tokens_to_arrow(
                    self._production,
                    self._variables if self._variables else []
                )

                # Convert Arrow table to pandas (zero-copy when possible)
                df = arrow_table.to_pandas()
                return df

            except Exception as e:
                # Fall back to Python conversion if Arrow fails
                pass

        # Fallback: Pure Python conversion (Week 2, Day 1-3)
        # Convert results to list of dicts
        data = self.to_list()

        # If no results, return empty DataFrame with columns
        if not data:
            return pd.DataFrame(columns=self._variables if self._variables else [])

        # Create DataFrame from list of dicts
        # This handles missing values gracefully
        df = pd.DataFrame(data)

        # Ensure columns are in the order of variables (if specified)
        if self._variables:
            # Only include requested variables
            df = df[self._variables]

        return df


# MergedQueryResultSet is now just an alias to C++ QueryResultSet
# Kept for backward compatibility
# Falls back to Python QueryResultSet if C++ version not available (requires Arrow support)
try:
    MergedQueryResultSet = owl_rete_cpp.QueryResultSet
except AttributeError:
    # C++ QueryResultSet not available (extension built without Arrow support)
    MergedQueryResultSet = QueryResultSet


class FilteredQueryResultSet:
    """
    Query result set with NOT EXISTS filtering (Week 5, Day 1-3 + Week 6 C++ optimization)
    Thin wrapper that delegates to C++ not_exists_query with Arrow anti-join

    Performance: 10-100x faster than Python implementation

    @reter-cnl: This is-in-layer Core-Layer.
    @reter-cnl: This is a wrapper.
    @reter-cnl: This is a public-application-programming-interface.
    """

    def __new__(cls, production, variables, network, not_exists_patterns, reasoner):
        """
        Args:
            production: ProductionNode from main query
            variables: List of variable names (e.g., ["?x", "?age"])
            network: ReteNetwork instance
            not_exists_patterns: List of patterns that must NOT match
            reasoner: Reter instance (needed to build NOT EXISTS productions)

        Returns:
            C++ QueryResultSet with NOT EXISTS filtering applied
        """
        # Build NOT EXISTS productions by using the reasoner's pattern method
        # This ensures proper handling of property type detection
        not_exists_productions = []
        for pattern in not_exists_patterns:
            # Use reasoner.pattern() to build the production with proper Condition objects
            result_set = reasoner.pattern(pattern)
            # Extract the production from the result set
            # QueryResultSet has _production attribute
            if hasattr(result_set, '_production'):
                not_exists_productions.append(result_set._production)
            else:
                raise RuntimeError("Could not extract production from NOT EXISTS pattern")

        # Extract all variables from NOT EXISTS patterns
        def get_vars(pattern):
            """Extract variable names from a pattern"""
            return {elem for elem in pattern if isinstance(elem, str) and elem.startswith("?")}

        # Collect all variables that appear in both main query and NOT EXISTS patterns
        main_vars = set(variables)
        not_exists_vars = set()
        for pattern in not_exists_patterns:
            not_exists_vars.update(get_vars(pattern))

        # Shared variables are those in both main and NOT EXISTS
        shared_vars = sorted(main_vars & not_exists_vars)

        # Delegate to C++ not_exists_query with Arrow anti-join
        return network.not_exists_query(
            production,
            not_exists_productions,
            variables,
            shared_vars
        )


class UnionQueryResultSet:
    """
    Query result set combining multiple queries with UNION (Week 5, Day 4-5)
    Merges results from multiple QueryResultSets with deduplication

    Week 6 Optimization: Thin wrapper delegating to C++ union_query

    @reter-cnl: This is-in-layer Core-Layer.
    @reter-cnl: This is a data-transformer.
    """

    def __new__(cls, queries, network):
        """
        Args:
            queries: List/tuple of QueryResultSet objects to combine
            network: ReteNetwork instance

        Returns:
            C++ QueryResultSet with union of all queries
        """
        # Extract productions and variables from queries
        # Works with both old Python QueryResultSet and new C++ QueryResultSet (both have _production now)
        productions = []
        all_variables = set()

        for query in queries:
            if hasattr(query, '_production') and query._production:
                productions.append(query._production)
            if hasattr(query, '_variables') and query._variables:
                all_variables.update(query._variables)

        if not productions:
            raise ValueError("UnionQueryResultSet requires at least one query with a production")

        variables = sorted(all_variables)

        # Use C++ union_query - returns C++ QueryResultSet directly
        return network.union_query(productions, variables)


class PropertyPathResultSet:
    """
    Query result set for property paths (Week 5, Day 6-7)
    Computes transitive closure of a property using BFS

    @reter-cnl: This is-in-layer Core-Layer.
    @reter-cnl: This is a query-executor.
    """

    def __init__(self, subject, property_name, object_var, max_depth, reasoner):
        """
        Args:
            subject: Start node (constant or variable)
            property_name: Property to traverse (e.g., "hasParent")
            object_var: End node variable (e.g., "?ancestor")
            max_depth: Maximum recursion depth
            reasoner: Reter instance
        """
        self._subject = subject
        self._property = property_name
        self._object_var = object_var
        self._max_depth = max_depth
        self._reasoner = reasoner

    def _compute_transitive_closure(self):
        """Compute transitive closure using BFS"""
        results = []

        # If subject is a variable, get all starting points
        if self._subject.startswith("?"):
            # Get all individuals that have this property
            start_query = self._reasoner.pattern((self._subject, self._property, "?_obj"))
            start_nodes = {r[self._subject] for r in start_query.to_list()}
        else:
            start_nodes = {self._subject}

        # For each starting node, perform BFS
        for start_node in start_nodes:
            visited = set()
            queue = [(start_node, 0)]  # (node, depth)

            while queue:
                current, depth = queue.pop(0)

                # Skip if already visited or max depth reached
                if current in visited or depth >= self._max_depth:
                    continue

                visited.add(current)

                # Query for direct successors via this property
                successor_query = self._reasoner.pattern((current, self._property, "?next"))
                successors = successor_query.to_list()

                for s in successors:
                    next_node = s["?next"]

                    # Add to results (excluding start node itself unless reflexive)
                    if next_node != start_node or depth > 0:
                        result = {}
                        if self._subject.startswith("?"):
                            result[self._subject] = start_node
                        result[self._object_var] = next_node

                        # Check if we already have this result
                        if result not in results:
                            results.append(result)

                    # Add to queue for further exploration
                    if next_node not in visited and depth + 1 < self._max_depth:
                        queue.append((next_node, depth + 1))

        return results

    def __iter__(self):
        """Iterate over transitive closure results"""
        for result in self._compute_transitive_closure():
            yield result

    def __len__(self):
        """Number of reachable nodes"""
        return len(self._compute_transitive_closure())

    def __repr__(self):
        return f"PropertyPathResultSet({len(self)} reachable nodes, max_depth={self._max_depth})"

    def to_list(self):
        """Convert to list of dicts"""
        return self._compute_transitive_closure()

    def to_pandas(self):
        """
        Convert property path results to pandas DataFrame

        Returns:
            pandas.DataFrame with columns for subject and object
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas is required for to_pandas(). Install with: pip install pandas")

        # Get transitive closure results
        data = self.to_list()

        # If no results, return empty DataFrame
        if not data:
            columns = [self._object_var]
            if self._subject.startswith("?"):
                columns.insert(0, self._subject)
            return pd.DataFrame(columns=columns)

        # Create DataFrame from list of dicts
        df = pd.DataFrame(data)

        return df


class LiveQueryResultSet:
    """
    Auto-updating query result set (Week 4, Day 4-7)
    Results update incrementally as facts are added/removed

    @reter-cnl: This is-in-layer Core-Layer.
    @reter-cnl: This is a observer.
    """

    def __init__(self, live_query, variables, network):
        """
        Args:
            live_query: C++ LiveQuery object
            variables: List of variable names (e.g., ["?x", "?age"])
            network: ReteNetwork instance
        """
        self._live_query = live_query
        self._variables = variables
        self._network = network
        self._callbacks = []

    def __len__(self):
        """Number of current results"""
        return self._live_query.size()

    def __iter__(self):
        """Iterate over current results"""
        tokens = self._live_query.get_results()
        cache_key = self._live_query.cache_key()

        for token in tokens:
            # Extract bindings from token using cache_key
            bindings = self._network.extract_bindings(cache_key, token)

            # Return only requested variables
            if self._variables:
                yield {v: bindings.get(v, None) for v in self._variables}
            else:
                yield bindings

    def __repr__(self):
        return f"LiveQueryResultSet({len(self)} results, variables={self._variables})"

    def on_change(self, callback):
        """
        Register callback for result changes

        Args:
            callback: Function called when results change
                     Signature: callback(token, is_addition)

        Example:
            def on_update(token, is_addition):
                if is_addition:
                    print(f"Added: {token.get_all_bindings()}")
                else:
                    print(f"Removed: {token.get_all_bindings()}")

            live.on_change(on_update)
        """
        self._live_query.on_change(callback)
        self._callbacks.append(callback)

    def to_list(self):
        """Snapshot of current results as list"""
        return list(self)

    def to_pandas(self):
        """Snapshot of current results as pandas DataFrame"""
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas is required for to_pandas()")

        # Get current data
        data = self.to_list()

        # If no results, return empty DataFrame with columns
        if not data:
            return pd.DataFrame(columns=self._variables if self._variables else [])

        # Create DataFrame from list of dicts
        df = pd.DataFrame(data)

        # Ensure columns are in the order of variables (if specified)
        if self._variables:
            df = df[self._variables]

        return df


class Reter:
    """
    Main Description Logic Reasoner
    Uses C++ DL parser and C++ OWL RETE reasoning engine directly

    @reter-cnl: This is-in-layer Core-Layer.
    @reter-cnl: This is a description-logic-reasoner.
    @reter-cnl: This depends-on `reter_core.owl_rete_cpp.ReteNetwork`.
    """

    # Expose C++ compilation flags
    OWL_THING_REASONING_ENABLED = owl_rete_cpp.OWL_THING_REASONING_ENABLED

    def __init__(self, variant="unicode"):
        """
        Initialize the reasoner with C++ RETE network

        Args:
            variant: Parser syntax variant - 'unicode' (default), 'ascii', or 'ai'
                    - 'unicode': Full Unicode symbols (⊑, ∃, etc.)
                    - 'ascii': ASCII-friendly (is_subclass_of, some, etc.)
                    - 'ai': AI-friendly with programming language identifiers
        """
        self.network = owl_rete_cpp.ReteNetwork()
        self.variant = variant

    def load_ontology_file(self, filepath):
        """
        Load and parse DL ontology from file using C++ parser

        Args:
            filepath: Path to DL ontology file

        Returns:
            Number of WMEs added
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        return self.load_ontology(content)

    def load_ontology(self, dl_text, source=None):
        """
        Parse DL text and add to RETE network using C++ parser

        Args:
            dl_text: Description Logic statements as text
            source: Optional source identifier for tracking

        Returns:
            Number of WMEs added
        """
        try:
            # Use C++ parser with optional source tracking and variant
            if source is None:
                wme_count = self.network.load_ontology_from_string(dl_text, variant=self.variant)
            else:
                wme_count = self.network.load_ontology_from_string_with_source(dl_text, source, variant=self.variant)
            return wme_count

        except Exception as e:
            raise RuntimeError(f"Failed to load ontology: {e}")

    def load_cnl(self, cnl_text, source=None):
        """
        Parse CNL (Controlled Natural Language) text and add to RETE network

        CNL provides an English-like syntax for ontology statements:
            Every cat is a mammal.           (subsumption)
            John is a person.                (instance assertion)
            Mary is-married-to John.         (role assertion)
            John has-age equal-to 30.        (data assertion)

        Supports backtick-quoted identifiers for namespaced concepts:
            Every `py:Method` is a `py:Function`.
            Every `oo:Class` is a `owl:Thing`.

        Args:
            cnl_text: CNL statements as text
            source: Optional source identifier for tracking

        Returns:
            Number of WMEs added

        Example:
            reasoner = Reter()
            reasoner.load_cnl('''
                Every cat is a mammal.
                Every dog is a mammal.
                Felix is a cat.
            ''')
        """
        try:
            # Parse CNL to get facts
            result = owl_rete_cpp.parse_cnl(cnl_text)

            # Add each fact to the network
            wme_count = 0
            for fact_obj in result.facts:
                # Convert ParsedFact to Fact dict
                fact_dict = {}
                for key in fact_obj.keys():
                    fact_dict[key] = fact_obj.get(key)

                fact = owl_rete_cpp.Fact(fact_dict)

                if source is None:
                    self.network.add_fact(fact)
                else:
                    self.network.add_fact_with_source(fact, source)
                wme_count += 1

            return wme_count

        except Exception as e:
            raise RuntimeError(f"Failed to load CNL: {e}")

    def load_cnl_file(self, filepath, source=None):
        """
        Load and parse CNL ontology from file

        Args:
            filepath: Path to CNL ontology file (.cnl)
            source: Optional source identifier (defaults to filepath)

        Returns:
            Number of WMEs added

        Example:
            reasoner = Reter()
            reasoner.load_cnl_file("ontology.cnl")
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Use filepath as source if not specified
        if source is None:
            source = filepath

        return self.load_cnl(content, source)

    def analyze_python_code(self, python_code, module_name="module"):
        """
        Analyze Python source code and return facts and errors without adding to network

        Args:
            python_code: Python source code as string
            module_name: Module name for the code

        Returns:
            Tuple of (facts, errors) where:
            - facts: List of extracted fact dictionaries
            - errors: List of syntax error dictionaries (empty if no errors)

        Example:
            reasoner = Reter()

            code = '''
            class Animal:
                def speak(self):
                    return "..."
            '''

            facts, errors = reasoner.analyze_python_code(code, "animals")

            if errors:
                print("Syntax errors:")
                for err in errors:
                    print(f"  Line {err['line']}: {err['message']}")
            else:
                print(f"Successfully parsed {len(facts)} facts")
                for fact in facts:
                    print(f"  {fact}")
        """
        from reter_core import owl_rete_cpp
        # Pass module_name as both in_file and module_name for backward compatibility
        # (when used standalone without file path context)
        in_file = module_name + ".py" if not module_name.endswith(".py") else module_name
        return owl_rete_cpp.parse_python_code(python_code, in_file, module_name)

    def load_python_file(self, filepath, module_name=None, progress_callback=None):
        """
        Load and parse Python source file, extracting semantic facts

        Args:
            filepath: Path to Python source file
            module_name: Optional module name (defaults to filename without .py)
            progress_callback: Optional callback function(items_processed, total_items, message)

        Returns:
            Tuple of (wme_count, errors) where:
            - wme_count: Number of WMEs added from the Python file
            - errors: List of syntax error dictionaries (empty if no errors)

        Example:
            reasoner = Reter()
            reasoner.load_ontology_file("py_ontology.dl")  # Load Python ontology

            def on_progress(processed, total, msg):
                print(f"Progress: {processed}/{total} - {msg}")

            wme_count, errors = reasoner.load_python_file("my_module.py", progress_callback=on_progress)

            if errors:
                print(f"Errors in {filepath}:")
                for err in errors:
                    print(f"  Line {err['line']}: {err['message']}")
        """
        import os

        # Use filepath as in_file (normalized to forward slashes)
        in_file = filepath.replace("\\", "/")

        # Default module_name from filepath if not provided
        if module_name is None:
            module_name = os.path.splitext(os.path.basename(filepath))[0]

        with open(filepath, 'r', encoding='utf-8') as f:
            python_code = f.read()

        # Call load_python_code with correct parameters
        return self.load_python_code(python_code, in_file, module_name, None, progress_callback)

    def load_python_code(self, python_code, in_file="module.py", module_name=None, source_id=None, progress_callback=None):
        """
        Parse Python source code and extract semantic facts

        Args:
            python_code: Python source code as string
            in_file: Relative file path (e.g., "path/to/file.py") stored in inFile attribute
            module_name: Python module name (e.g., "path.to.file") stored in moduleName attribute.
                        If None, derived from in_file by replacing "/" with "." and removing ".py"
            source_id: Optional source identifier for tracking (defaults to in_file).
                       Should be in format "md5|path" for proper file change detection.
            progress_callback: Optional callback function(items_processed, total_items, message)

        Returns:
            Tuple of (wme_count, errors) where:
            - wme_count: Number of WMEs added from the Python code
            - errors: List of syntax error dictionaries (empty if no errors)

        Example:
            reasoner = Reter()
            reasoner.load_ontology_file("py_ontology.dl")

            code = '''
            class Animal:
                def speak(self):
                    return "..."
            '''

            def on_progress(processed, total, msg):
                print(f"Progress: {processed}/{total} - {msg}")

            wme_count, errors = reasoner.load_python_code(code, "animals.py", "animals", progress_callback=on_progress)

            if errors:
                for err in errors:
                    print(f"  Line {err['line']}: {err['message']}")
            else:
                print(f"Successfully loaded {wme_count} WMEs")

            # Now query the extracted facts
            classes = reasoner.pattern(("?x", "type", "py:Class"))
        """
        # Use parse_python_code that returns (facts, errors, registered_methods, unresolved_calls)
        from reter_core import owl_rete_cpp

        # Derive module_name from in_file if not provided
        if module_name is None:
            module_name = in_file
            if module_name.endswith(".py"):
                module_name = module_name[:-3]
            module_name = module_name.replace("/", ".").replace("\\", ".")

        facts, errors, registered_methods, unresolved_calls = owl_rete_cpp.parse_python_code(python_code, in_file, module_name)

        # Use source_id if provided, otherwise fall back to in_file
        actual_source_id = source_id if source_id is not None else in_file

        # Calculate total items for progress reporting
        total_items = len(facts) + len(registered_methods) + len(unresolved_calls)
        items_processed = 0

        # Add facts to the network
        wme_count = 0
        for fact in facts:
            self.network.add_fact_with_source(
                owl_rete_cpp.Fact(fact),
                actual_source_id  # Use source_id for tracking
            )
            wme_count += 1
            items_processed += 1
            if progress_callback and items_processed % 100 == 0:
                progress_callback(items_processed, total_items, f"Adding facts from {in_file}")

        # Register methods for maybeCalls resolution
        for method in registered_methods:
            self.network.register_method_for_maybe_calls(
                method["entity_id"],
                method["name"],
                method["param_count"],
                method["module"],
                method["class_name"]
            )
            items_processed += 1

        if progress_callback and registered_methods:
            progress_callback(items_processed, total_items, f"Registered {len(registered_methods)} methods")

        # Add pending calls for maybeCalls resolution
        for call in unresolved_calls:
            self.network.add_pending_call(
                call["caller_entity_id"],
                call["method_name"],
                call["arg_count"],
                call["caller_module"],
                call["caller_class"]
            )
            items_processed += 1

        if progress_callback:
            progress_callback(total_items, total_items, f"Completed {in_file}: {wme_count} WMEs")

        return wme_count, errors

    def load_python_directory(self, directory, recursive=True, progress_callback=None):
        """
        Load all Python files from a directory

        Args:
            directory: Path to directory containing Python files
            recursive: If True, recursively scan subdirectories
            progress_callback: Optional callback function(items_processed, total_items, message)

        Returns:
            Tuple of (total_wmes, all_errors) where:
            - total_wmes: Total number of WMEs added from all Python files
            - all_errors: Dict mapping filepath -> list of errors

        Example:
            reasoner = Reter()
            reasoner.load_ontology_file("py_ontology.dl")

            def on_progress(processed, total, msg):
                print(f"{processed}/{total}: {msg}")

            total_wmes, all_errors = reasoner.load_python_directory("src/", recursive=True, progress_callback=on_progress)

            print(f"Loaded {total_wmes} WMEs from Python files")

            if all_errors:
                print(f"\nFound syntax errors in {len(all_errors)} files:")
                for filepath, errors in all_errors.items():
                    print(f"  {filepath}:")
                    for err in errors:
                        print(f"    Line {err['line']}: {err['message']}")

            # Query all classes in the codebase
            classes = reasoner.pattern(
                ("?class", "type", "py:Class"),
                ("?class", "name", "?name")
            )
        """
        import os
        import glob

        total_wmes = 0
        all_errors = {}
        pattern = "**/*.py" if recursive else "*.py"

        for filepath in glob.glob(os.path.join(directory, pattern), recursive=recursive):
            # Skip __pycache__ directories
            if "__pycache__" in filepath:
                continue

            # Generate module name from relative path
            rel_path = os.path.relpath(filepath, directory)
            module_name = rel_path.replace(os.sep, ".").replace(".py", "")

            wmes, errors = self.load_python_file(filepath, module_name, progress_callback)
            total_wmes += wmes

            # Collect errors for this file
            if errors:
                all_errors[filepath] = errors

        return total_wmes, all_errors

    def load_csharp_code(self, csharp_code, namespace_name="global", progress_callback=None):
        """Parse C# source code and extract semantic facts

        Args:
            csharp_code: C# source code as string
            namespace_name: Namespace name for the code
            progress_callback: Optional callback function(items_processed, total_items, message)

        Returns:
            Number of WMEs added from the C# code
        """
        try:
            from reter_core import owl_rete_cpp
            wme_count = owl_rete_cpp.load_csharp_from_string(
                self.network,
                csharp_code,
                namespace_name,
                progress_callback=progress_callback
            )
            return wme_count
        except Exception as e:
            raise RuntimeError(f"Failed to load C# code: {e}")

    def load_cpp_code(self, cpp_code, namespace_name="global", progress_callback=None):
        """Parse C++ source code and extract semantic facts

        Args:
            cpp_code: C++ source code as string
            namespace_name: Namespace name for the code
            progress_callback: Optional callback function(items_processed, total_items, message)

        Returns:
            Number of WMEs added from the C++ code
        """
        try:
            from reter_core import owl_rete_cpp
            wme_count = owl_rete_cpp.load_cpp_from_string(
                self.network,
                cpp_code,
                namespace_name,
                progress_callback=progress_callback
            )
            return wme_count
        except Exception as e:
            raise RuntimeError(f"Failed to load C++ code: {e}")

    def load_javascript_code(self, javascript_code, module_name="module", progress_callback=None):
        """Parse JavaScript source code and extract semantic facts

        Args:
            javascript_code: JavaScript source code as string
            module_name: Module name for the code
            progress_callback: Optional callback function(items_processed, total_items, message)

        Returns:
            Number of WMEs added from the JavaScript code
        """
        try:
            from reter_core import owl_rete_cpp
            wme_count = owl_rete_cpp.load_javascript_from_string(
                self.network,
                javascript_code,
                module_name,
                progress_callback=progress_callback
            )
            return wme_count
        except Exception as e:
            raise RuntimeError(f"Failed to load JavaScript code: {e}")

    def load_csharp_file(self, filepath, namespace_name=None, progress_callback=None):
        """Load C# file and extract facts

        Args:
            filepath: Path to C# file
            namespace_name: Optional namespace name (uses filename if not provided)
            progress_callback: Optional callback function(items_processed, total_items, message)

        Returns:
            Number of WMEs added from the C# file
        """
        import os
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()

        if namespace_name is None:
            namespace_name = os.path.splitext(os.path.basename(filepath))[0]

        return self.load_csharp_code(code, namespace_name, progress_callback)

    def load_csharp_directory(self, directory, recursive=True):
        """Load all C# files from a directory

        Args:
            directory: Directory path
            recursive: Whether to search subdirectories

        Returns:
            Total number of WMEs added
        """
        import os
        total_wmes = 0

        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.cs'):
                    filepath = os.path.join(root, file)
                    try:
                        wmes = self.load_csharp_file(filepath)
                        total_wmes += wmes
                    except Exception as e:
                        pass

            if not recursive:
                break

        return total_wmes

    def load_cpp_file(self, filepath, namespace_name=None, progress_callback=None):
        """Load C++ file and extract facts

        Args:
            filepath: Path to C++ file
            namespace_name: Optional namespace name (uses filename if not provided)
            progress_callback: Optional callback function(items_processed, total_items, message)

        Returns:
            Number of WMEs added from the C++ file
        """
        import os
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()

        if namespace_name is None:
            namespace_name = os.path.splitext(os.path.basename(filepath))[0]

        return self.load_cpp_code(code, namespace_name, progress_callback)

    def load_cpp_directory(self, directory, recursive=True):
        """Load all C++ files from a directory

        Args:
            directory: Directory path
            recursive: Whether to search subdirectories

        Returns:
            Total number of WMEs added
        """
        import os
        total_wmes = 0

        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(('.cpp', '.cc', '.cxx', '.h', '.hpp', '.hxx')):
                    filepath = os.path.join(root, file)
                    try:
                        wmes = self.load_cpp_file(filepath)
                        total_wmes += wmes
                    except Exception as e:
                        pass

            if not recursive:
                break

        return total_wmes

    def load_javascript_file(self, filepath, module_name=None, progress_callback=None):
        """Load JavaScript file and extract facts

        Args:
            filepath: Path to JavaScript file
            module_name: Optional module name (uses filename if not provided)
            progress_callback: Optional callback function(items_processed, total_items, message)

        Returns:
            Number of WMEs added from the JavaScript file
        """
        import os
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()

        if module_name is None:
            module_name = os.path.splitext(os.path.basename(filepath))[0]

        return self.load_javascript_code(code, module_name, progress_callback)

    def load_javascript_directory(self, directory, recursive=True):
        """Load all JavaScript files from a directory

        Args:
            directory: Directory path
            recursive: Whether to search subdirectories

        Returns:
            Total number of WMEs added
        """
        import os
        total_wmes = 0

        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(('.js', '.jsx', '.mjs')):
                    filepath = os.path.join(root, file)
                    try:
                        wmes = self.load_javascript_file(filepath)
                        total_wmes += wmes
                    except Exception as e:
                        pass

            if not recursive:
                break

        return total_wmes

    def load_html_code(self, html_code, in_file="page.html", progress_callback=None):
        """Parse HTML source code and extract semantic facts

        Args:
            html_code: HTML source code as string
            in_file: File name for the code (used in facts)
            progress_callback: Optional callback function(items_processed, total_items, message)

        Returns:
            Number of WMEs added from the HTML code
        """
        try:
            from reter_core import owl_rete_cpp
            wme_count = owl_rete_cpp.load_html_from_string(
                self.network,
                html_code,
                in_file,
                progress_callback=progress_callback
            )
            return wme_count
        except Exception as e:
            raise RuntimeError(f"Failed to load HTML code: {e}")

    def load_html_file(self, filepath, in_file=None, progress_callback=None):
        """Load HTML file and extract facts

        Args:
            filepath: Path to HTML file
            in_file: Optional file name for facts (uses filename if not provided)
            progress_callback: Optional callback function(items_processed, total_items, message)

        Returns:
            Number of WMEs added from the HTML file
        """
        import os
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()

        if in_file is None:
            in_file = os.path.basename(filepath)

        return self.load_html_code(code, in_file, progress_callback)

    def load_html_directory(self, directory, recursive=True):
        """Load all HTML files from a directory

        Args:
            directory: Directory path
            recursive: Whether to search subdirectories

        Returns:
            Total number of WMEs added
        """
        import os
        total_wmes = 0

        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(('.html', '.htm')):
                    filepath = os.path.join(root, file)
                    try:
                        wmes = self.load_html_file(filepath)
                        total_wmes += wmes
                    except Exception as e:
                        pass

            if not recursive:
                break

        return total_wmes

    def add_fact(self, fact_dict, source=None):
        """
        Add a single fact using a dictionary specification.
        Python wrapper for C++ add_fact() method.

        WARNING: This is a low-level API. For adding semantic triples, use add_triple() instead.
        This method expects facts with the internal RETE structure (e.g., with "type", "concept",
        "individual" attributes for instances, or "type", "property", "subject", "value" for data properties).

        Args:
            fact_dict: Dictionary describing the fact (string keys and values)
            source: Optional source identifier for tracking

        Returns:
            Fact ID assigned by the network

        See also:
            add_triple(): High-level API for adding semantic triples
        """
        # Convert dict to Fact object before passing to C++
        from reter_core import owl_rete_cpp
        fact = owl_rete_cpp.Fact(fact_dict)

        # Use source tracking if provided
        if source is None:
            return self.network.add_fact(fact)
        else:
            return self.network.add_fact_with_source(fact, source)

    def add_triple(self, subject, predicate, object_value, source=None):
        """
        Add a semantic triple in REQL-compatible format.

        This is the recommended API for adding facts programmatically.
        Automatically detects the triple type and creates the proper internal fact structure.

        Args:
            subject: Subject of the triple (e.g., "Alice", "Person")
            predicate: Predicate/property name (e.g., "type", "hasAge", "knows")
            object_value: Object of the triple (e.g., "Person", "30", "Bob")
            source: Optional source identifier for tracking

        Returns:
            Fact ID assigned by the network

        Examples:
            # Add instance assertion
            reasoner.add_triple("Alice", "type", "Person")
            # Creates: {"type": "instance_of", "individual": "Alice", "concept": "Person"}

            # Add data property assertion
            reasoner.add_triple("Alice", "hasAge", "30")
            # Creates: {"type": "data_assertion", "subject": "Alice", "property": "hasAge", "value": "30"}

            # Add object property assertion
            reasoner.add_triple("Alice", "knows", "Bob")
            # Creates: {"type": "role_assertion", "subject": "Alice", "role": "knows", "object": "Bob"}

            # With source tracking
            reasoner.add_triple("Alice", "type", "Person", source="my_data")
        """
        from reter_core import owl_rete_cpp

        # Detect triple type and create proper fact structure
        if predicate == "type":
            # Instance assertion: subject is an instance of object_value class
            fact_dict = {
                "type": "instance_of",
                "concept": object_value,
                "individual": subject
            }
        else:
            # Check if this is a known data property or object property
            # by inspecting existing facts in the network
            property_types = self._detect_property_types({predicate})
            prop_type = property_types.get(predicate)

            if prop_type == "data":
                # Data property assertion
                fact_dict = {
                    "type": "data_assertion",
                    "property": predicate,
                    "subject": subject,
                    "value": object_value
                }
            elif prop_type == "role":
                # Object property assertion
                fact_dict = {
                    "type": "role_assertion",
                    "role": predicate,
                    "subject": subject,
                    "object": object_value
                }
            elif prop_type == "same_as":
                # Same-as assertion
                fact_dict = {
                    "type": "same_as",
                    "ind1": subject,
                    "ind2": object_value
                }
            else:
                # Unknown property type - try to infer from object value
                # If object looks like a number or string literal, assume data property
                # Otherwise, assume object property
                try:
                    # Try to parse as number
                    float(object_value)
                    is_literal = True
                except (ValueError, TypeError):
                    # Not a number - check if it's clearly a literal (contains quotes, etc.)
                    is_literal = isinstance(object_value, str) and (
                        object_value.startswith('"') or object_value.startswith("'") or
                        object_value.isdigit()
                    )

                if is_literal:
                    # Assume data property
                    fact_dict = {
                        "type": "data_assertion",
                        "property": predicate,
                        "subject": subject,
                        "value": object_value
                    }
                else:
                    # Assume object property
                    fact_dict = {
                        "type": "role_assertion",
                        "role": predicate,
                        "subject": subject,
                        "object": object_value
                    }

        # Create fact and add to network
        fact = owl_rete_cpp.Fact(fact_dict)
        if source is None:
            return self.network.add_fact(fact)
        else:
            return self.network.add_fact_with_source(fact, source)

    def _detect_property_types(self, predicates):
        """
        Detect which predicates are role_assertion vs data_assertion vs same_as
        by inspecting actual facts in the network

        Args:
            predicates: Set of predicate names to check

        Returns:
            dict mapping predicate -> "role", "data", or "same_as"
        """
        property_types = {}

        # Check for same_as specially - it's a reserved predicate
        if "same_as" in predicates or "sameAs" in predicates:
            property_types["same_as"] = "same_as"
            property_types["sameAs"] = "same_as"

        for fact in self.network.get_all_facts():
            fact_type = fact.get("type")

            if fact_type == "role_assertion":
                role = fact.get("role")
                if role and role in predicates:
                    property_types[role] = "role"

            elif fact_type == "data_assertion":
                prop = fact.get("property")
                if prop and prop in predicates:
                    property_types[prop] = "data"

        return property_types

    def pattern(self, *patterns, cache=None, select=None, where=None, values=None, not_exists=None):
        """
        Query using graph patterns with optional filters, VALUES, and NOT EXISTS constraints

        Args:
            *patterns: Variable number of triple patterns
                      Each pattern is a tuple (subject, predicate, object)
                      Variables start with '?'
            cache: Optional cache key (auto-generated if None)
            select: Optional list of variables to return (all if None)
            where: Optional list of filter conditions
                  Each filter is a tuple (builtin_name, arg1, arg2, ...)
                  Example: [("greaterThan", "?age", "18")]
            values: Optional dict mapping variables to allowed values
                   Example: {"?city": ["NYC", "LA", "Chicago"]}
            not_exists: Optional list of patterns that must NOT match
                       Example: [("?x", "hasChild", "?y")]

        Returns:
            QueryResultSet for iteration or conversion

        Example:
            # Basic query
            results = r.pattern(
                ("?x", "type", "Person"),
                ("?x", "hasAge", "?age")
            )

            # Query with filters
            adults = r.pattern(
                ("?x", "type", "Person"),
                ("?x", "hasAge", "?age"),
                where=[("greaterThan", "?age", "18")]
            )

            # Query with VALUES constraint
            big_city_residents = r.pattern(
                ("?x", "livesIn", "?city"),
                values={"?city": ["NYC", "LA", "Chicago"]}
            )

            # Query with NOT EXISTS
            childless_people = r.pattern(
                ("?x", "type", "Person"),
                not_exists=[("?x", "hasChild", "?y")]
            )

            for binding in results:
                print(binding["?x"], binding["?age"])
        """
        # Auto-generate cache key if not provided
        # Use hash() instead of MD5 for much faster cache key generation
        if cache is None:
            # Create a hashable tuple representation
            # Convert values dict to hashable format (lists → tuples)
            hashable_values = None
            if values:
                hashable_values = tuple(
                    (k, tuple(v) if isinstance(v, list) else v)
                    for k, v in sorted(values.items())
                )

            cache_tuple = (patterns, tuple(where) if where else None,
                          hashable_values,
                          tuple(not_exists) if not_exists else None)
            cache = str(hash(cache_tuple))

        # Check if we have a cached production FIRST (before expensive work)
        cached_production = self.network.get_cached_query(cache)

        # Extract variables for return (needed even on cache hit)
        variables = set()
        for (subj, pred, obj) in patterns:
            if subj.startswith("?"):
                variables.add(subj)
            if obj.startswith("?"):
                variables.add(obj)

        if cached_production is None:
            # Cache miss - need to build the production
            # Convert triple patterns to Condition objects
            # First, detect property types by inspecting actual facts
            predicates = {pred for (subj, pred, obj) in patterns if pred != "type"}
            property_types = self._detect_property_types(predicates)

            conditions = []

            for (subj, pred, obj) in patterns:
                # Map triple pattern to WME conditions based on actual fact types

                if pred == "type":
                    # (?x, type, Person) maps to instance_of facts
                    fact_var = f"?f_{len(conditions)}"
                    conditions.append(owl_rete_cpp.Condition(fact_var, "type", "instance_of"))
                    conditions.append(owl_rete_cpp.Condition(fact_var, "concept", obj))
                    conditions.append(owl_rete_cpp.Condition(fact_var, "individual", subj))
                else:
                    # Use detected property type, with fallback to role_assertion
                    prop_type = property_types.get(pred, "role")  # Default to role if unknown

                    fact_var = f"?f_{len(conditions)}"
                    if prop_type == "same_as":
                        # same_as facts use ind1/ind2 fields
                        conditions.append(owl_rete_cpp.Condition(fact_var, "type", "same_as"))
                        conditions.append(owl_rete_cpp.Condition(fact_var, "ind1", subj))
                        conditions.append(owl_rete_cpp.Condition(fact_var, "ind2", obj))
                    elif prop_type == "data":
                        # Data property: data_assertion with subject, property, value
                        conditions.append(owl_rete_cpp.Condition(fact_var, "type", "data_assertion"))
                        conditions.append(owl_rete_cpp.Condition(fact_var, "property", pred))
                        conditions.append(owl_rete_cpp.Condition(fact_var, "subject", subj))
                        conditions.append(owl_rete_cpp.Condition(fact_var, "value", obj))
                    else:
                        # Object property: role_assertion with subject, role, object
                        conditions.append(owl_rete_cpp.Condition(fact_var, "type", "role_assertion"))
                        conditions.append(owl_rete_cpp.Condition(fact_var, "role", pred))
                        conditions.append(owl_rete_cpp.Condition(fact_var, "subject", subj))
                        conditions.append(owl_rete_cpp.Condition(fact_var, "object", obj))

                    # Variables already extracted above

            # Build query production (with filters, VALUES, or both)
            if values:
                values_specs = []
                for var, vals in values.items():
                    values_specs.append(owl_rete_cpp.ValuesSpec(var, vals))
                production = self.network.build_query_pattern_with_values(cache, conditions, values_specs)
            elif where:
                builtin_filters = [list(filter_spec) for filter_spec in where]
                production = self.network.build_query_pattern_with_filters(cache, conditions, builtin_filters)
            else:
                production = self.network.build_query_pattern(cache, conditions)
        else:
            # Cache hit - use the cached production
            production = cached_production

        # Determine which variables to return
        return_vars = select if select else sorted(variables)

        # If NOT EXISTS is specified, wrap in a FilteredQueryResultSet
        if not_exists:
            return FilteredQueryResultSet(
                cache,
                return_vars,
                self.network,
                not_exists_patterns=not_exists,
                reasoner=self
            )
        else:
            # Pre-fetch tokens once for better performance
            # This avoids calling get_query_results() on each iteration
            tokens = self.network.get_query_results(cache)
            return QueryResultSet(cache, return_vars, self.network, tokens=tokens)

    def query(self, type=None, **kwargs):
        """
        Efficient query method using C++ Arrow-based filtering

        Queries facts by type and optional filters.
        Returns a list of matching facts as dictionaries.

        Args:
            type: Fact type to query (e.g., 'instance_of', 'role_assertion',
                  'property_domain', 'property_range')
            **kwargs: Additional filters (e.g., concept='Person', individual='john')

        Returns:
            list of fact dictionaries

        Examples:
            # Query all instances of a concept
            facts = r.query(type='instance_of', concept='Person')

            # Query role assertions
            facts = r.query(type='role_assertion', role='hasParent')

            # Query property domains
            domains = r.query(type='property_domain', property='hasParent')
        """
        # Python-side filtering (safe and reliable)
        # TODO: Optimize with C++ Arrow query when stable
        all_facts = list(self.network.get_all_facts())

        # Filter by type if specified
        if type is not None:
            all_facts = [f for f in all_facts if f.get('type') == type]

        # Filter by additional kwargs
        for key, value in kwargs.items():
            all_facts = [f for f in all_facts if f.get(key) == value]

        return all_facts

    def union(self, *queries):
        """
        Combine multiple query results using UNION (OR semantics)

        Merges results from multiple QueryResultSet objects and removes duplicates.
        This is equivalent to SQL UNION or SPARQL UNION.

        Args:
            *queries: Variable number of QueryResultSet objects to combine
                     All queries should have compatible variable names

        Returns:
            UnionQueryResultSet with merged results

        Example:
            # Get all people or students
            people = r.pattern(("?x", "type", "Person"))
            students = r.pattern(("?x", "type", "Student"))
            all_individuals = r.union(people, students)

            # Get young OR old people (age <= 25 OR age >= 65)
            young = r.pattern(
                ("?x", "type", "Person"),
                ("?x", "hasAge", "?age"),
                where=[("≤", "?age", "25")]
            )
            old = r.pattern(
                ("?x", "type", "Person"),
                ("?x", "hasAge", "?age"),
                where=[("≥", "?age", "65")]
            )
            result = r.union(young, old)
        """
        return UnionQueryResultSet(queries, self.network)

    def property_path(self, subject, path, object, max_depth=10):
        """
        Query transitive relationships using property paths

        Finds all reachable nodes through transitive closure of a property.
        For example, "hasParent*" finds all ancestors, "knows*" finds all transitively connected people.

        Args:
            subject: Start node (constant like "john" or variable like "?x")
            path: Property path expression (e.g., "hasParent*")
                 Currently only supports simple transitive paths (property*)
            object: End node variable (e.g., "?ancestor")
            max_depth: Maximum recursion depth (default 10)

        Returns:
            PropertyPathResultSet with (subject, object) pairs

        Example:
            # Find all ancestors of john
            ancestors = r.property_path("john", "hasParent*", "?ancestor")

            # Find all (person, ancestor) pairs
            all_ancestors = r.property_path("?person", "hasParent*", "?ancestor")

            # Limit depth to immediate parents and grandparents only
            close_ancestors = r.property_path("john", "hasParent*", "?ancestor", max_depth=2)
        """
        # Parse path expression
        if not path.endswith("*"):
            raise ValueError(f"Only transitive paths (path*) are currently supported, got: {path}")

        property_name = path[:-1]  # Remove the * suffix

        return PropertyPathResultSet(subject, property_name, object, max_depth, self)

    # ========================================================================
    # REQL Query Interface
    # SPARQL-inspired query language for RETE networks
    # REQL = RETE Query Language (adapted for Description Logic, not RDF)
    # ========================================================================

    def reql(self, query_string, timeout_ms=0):
        """
        Execute a REQL query (SELECT, ASK, or DESCRIBE) and return results as Arrow table

        REQL (RETE Query Language) is a SPARQL-inspired query language
        designed for Description Logic and RETE networks (not RDF).

        Parses REQL query string and executes it using the RETE network's
        pattern matching with Arrow-optimized result processing.

        Args:
            query_string: REQL query string (SELECT, ASK, or DESCRIBE syntax)
            timeout_ms: Query timeout in milliseconds. Default 0 means no timeout (infinite).
                       If the query exceeds this timeout, a RuntimeError is raised.

        Returns:
            pyarrow.Table with query results
            - SELECT queries: table with result columns
            - ASK queries: single-row table with 'result' column (boolean)
            - DESCRIBE queries: table with columns: subject, predicate, object, object_type

        Raises:
            RuntimeError: If the query times out (when timeout_ms > 0)

        Example:
            # Basic SELECT query
            result = r.reql("SELECT ?x WHERE { ?x type Person }")
            print(result.to_pydict())
            # Output: {'?x': ['alice', 'bob']}

            # Query with timeout (5 second limit)
            result = r.reql("SELECT ?x WHERE { ?x type Person }", timeout_ms=5000)

            # ASK query (checks if pattern exists)
            result = r.reql("ASK WHERE { ?x type Person }")
            exists = result['result'][0].as_py()  # True or False
            # Or: result.to_pandas()['result'][0]

            # Multiple patterns (join)
            result = r.reql('''
                SELECT ?x WHERE {
                    ?x type Person .
                    ?x type Doctor
                }
            ''')

            # UNION (disjunction)
            result = r.reql('''
                SELECT ?x WHERE {
                    { ?x type Person }
                    UNION
                    { ?x type Doctor }
                }
            ''')

            # OPTIONAL (left-join semantics)
            result = r.reql('''
                SELECT ?x ?email WHERE {
                    ?x type Person .
                    OPTIONAL { ?x hasEmail ?email }
                }
            ''')

            # MINUS (negation)
            result = r.reql('''
                SELECT ?x WHERE {
                    ?x type Person .
                    MINUS { ?x type Doctor }
                }
            ''')

            # Result modifiers
            result = r.reql('''
                SELECT DISTINCT ?x WHERE { ?x type Person }
                ORDER BY ?x
                LIMIT 10
                OFFSET 5
            ''')

            # DESCRIBE - get all facts about a resource
            result = r.reql("DESCRIBE Alice")
            # Returns table with columns: subject, predicate, object, object_type
            print(result.to_pandas())
            # Example output:
            #   subject predicate    object    object_type
            #   Alice   type         Person    entity
            #   Alice   age          30        number
            #   Alice   hasChild     Bob       entity

            # DESCRIBE with WHERE clause - describe all doctors
            result = r.reql('''
                DESCRIBE ?person WHERE {
                    ?person type Doctor
                }
            ''')

            # DESCRIBE multiple resources
            result = r.reql("DESCRIBE Alice Bob Charlie")

            # Convert to pandas
            import pandas as pd
            df = result.to_pandas()

            # Use Arrow compute functions
            import pyarrow.compute as pc
            filtered = pc.filter(result, pc.field('?x') != 'bob')
        """
        return self.network.reql_query(query_string, timeout_ms)

    # ========================================================================
    # Description Logic Query Interface
    # High-level DL expression queries translated to SPARQL
    # ========================================================================

    def dl_query(self, dl_expression):
        """
        Query using Description Logic expression syntax

        Translates DL expressions to SPARQL queries and executes them on the RETE network.
        Uses the syntax variant specified when the Reter instance was created.

        Args:
            dl_expression: DL expression string (syntax depends on variant)

        Returns:
            pyarrow.Table with query results (?x0 variable contains matches)

        Syntax depends on variant:
            Unicode (variant='unicode'):
                ⊓ (U+2293) - Conjunction (AND)
                ⊔ (U+2294) - Disjunction (OR)
                ¬ (U+00AC) - Negation (NOT)
                ∃ (U+2203) - Existential quantifier (some)

            ASCII (variant='ascii'):
                and - Conjunction
                or - Disjunction
                not - Negation
                some - Existential quantifier

            AI-friendly (variant='ai'):
                and - Conjunction
                or - Disjunction
                not - Negation
                some - Existential quantifier
                (Plus support for programming language identifiers)

        Examples:
            # Unicode syntax
            r = Reter(variant='unicode')
            result = r.dl_query("Person ⊓ Doctor")

            # ASCII syntax
            r = Reter(variant='ascii')
            result = r.dl_query("Person and Doctor")

            # AI-friendly syntax with programming identifiers
            r = Reter(variant='ai')
            result = r.dl_query("com.example.Person and Doctor")
            result = r.dl_query("some hasChild.Doctor")

            # Convert to pandas
            import pandas as pd
            df = result.to_pandas()
        """
        return owl_rete_cpp.dl_query(self.network, dl_expression, self.variant)

    def dl_ask(self, dl_expression):
        """
        Check existence using Description Logic expression

        Uses the syntax variant specified when the Reter instance was created.

        Args:
            dl_expression: DL expression string (syntax depends on variant)

        Returns:
            dict: Dictionary with 'result' key containing boolean value

        Examples:
            # Unicode syntax
            r = Reter(variant='unicode')
            result = r.dl_ask("Person ⊓ Doctor")
            # Returns: {"result": True} or {"result": False}

            # ASCII syntax
            r = Reter(variant='ascii')
            result = r.dl_ask("Person and Doctor")

            # AI-friendly syntax
            r = Reter(variant='ai')
            result = r.dl_ask("com.example.Person and Doctor")
            result = r.dl_ask("some hasChild.Doctor")
        """
        result = owl_rete_cpp.dl_ask(self.network, dl_expression, self.variant)
        return {"result": result}

    # ========================================================================
    # Template Query Methods (Week 3, Day 3-5)
    # Ultra-fast pre-compiled query templates with ~1μs performance
    # ========================================================================

    def instances_of(self, class_name):
        """
        Ultra-fast template query: Get all instances of a class

        Pattern compiled once on first call, cached for ~1μs subsequent calls.

        Args:
            class_name: Name of the class (e.g., "Person")

        Returns:
            QueryResultSet with ?x bound to individuals

        Example:
            people = r.instances_of("Person")
            for binding in people:
                print(binding["?x"])

            # Convert to pandas
            df = people.to_pandas()
        """
        # Call C++ template function to get tokens directly
        tokens = owl_rete_cpp.instances_of(self.network, class_name)

        # Use cache key for binding extraction
        cache_key = f"template:instances_of:{class_name}"

        # Wrap in QueryResultSet with pre-fetched tokens
        return QueryResultSet(cache_key, ["?x"], self.network, tokens=tokens)

    def related(self, subject, property_name):
        """
        Ultra-fast template query: Get all objects related via a property

        Pattern compiled once on first call, cached for ~1μs subsequent calls.

        Args:
            subject: Individual name (e.g., "john")
            property_name: Property name (e.g., "hasParent")

        Returns:
            QueryResultSet with ?y bound to related objects

        Example:
            parents = r.related("john", "hasParent")
            for binding in parents:
                print(binding["?y"])
        """
        tokens = owl_rete_cpp.related(self.network, subject, property_name)

        cache_key = f"template:related:{subject}:{property_name}"

        return QueryResultSet(cache_key, ["?y"], self.network, tokens=tokens)

    def property_value(self, subject, property_name):
        """
        Ultra-fast template query: Get property value for an individual

        Pattern compiled once on first call, cached for ~1μs subsequent calls.

        Args:
            subject: Individual name (e.g., "john")
            property_name: Property name (e.g., "hasAge")

        Returns:
            QueryResultSet with ?val bound to property value

        Example:
            age_result = r.property_value("john", "hasAge")
            for binding in age_result:
                print(f"John's age: {binding['?val']}")
        """
        tokens = owl_rete_cpp.property_value(self.network, subject, property_name)

        cache_key = f"template:property_value:{subject}:{property_name}"

        return QueryResultSet(cache_key, ["?val"], self.network, tokens=tokens)

    def instances_with_property(self, class_name, property_name):
        """
        Ultra-fast template query: Find all instances that have a specific property

        Pattern compiled once on first call, cached for ~1μs subsequent calls.

        Args:
            class_name: Class name (e.g., "Person")
            property_name: Property name (e.g., "hasAge")

        Returns:
            QueryResultSet with ?x (individual) and ?val (value)

        Example:
            people_with_age = r.instances_with_property("Person", "hasAge")
            for binding in people_with_age:
                print(f"{binding['?x']} has age {binding['?val']}")

            # Convert to pandas for analysis
            df = people_with_age.to_pandas()
            df["age_numeric"] = pd.to_numeric(df["?val"])
            print(f"Average age: {df['age_numeric'].mean()}")
        """
        tokens = owl_rete_cpp.instances_with_property(self.network, class_name, property_name)

        cache_key = f"template:instances_with_property:{class_name}:{property_name}"

        return QueryResultSet(cache_key, ["?x", "?val"], self.network, tokens=tokens)

    def all_property_assertions(self, property_name):
        """
        Ultra-fast template query: Find all property assertions of a given type

        Pattern compiled once on first call, cached for ~1μs subsequent calls.

        Args:
            property_name: Property name (e.g., "hasParent")

        Returns:
            QueryResultSet with ?x (subject) and ?y (object)

        Example:
            all_parents = r.all_property_assertions("hasParent")
            for binding in all_parents:
                print(f"{binding['?x']} has parent {binding['?y']}")

            # Convert to pandas for graph analysis
            df = all_parents.to_pandas()
        """
        tokens = owl_rete_cpp.all_property_assertions(self.network, property_name)

        cache_key = f"template:all_property:{property_name}"

        return QueryResultSet(cache_key, ["?x", "?y"], self.network, tokens=tokens)

    # ========================================================================
    # Live Query Methods (Week 4, Day 4-7)
    # Auto-updating result sets that track fact changes incrementally
    # ========================================================================

    def live_pattern(self, *patterns, cache=None, select=None, where=None):
        """
        Create a live query that auto-updates as facts change

        Args:
            *patterns: Variable number of triple patterns
                      Each pattern is a tuple (subject, predicate, object)
                      Variables start with '?'
            cache: Optional cache key (auto-generated if None)
            select: Optional list of variables to return (all if None)
            where: Optional list of filter conditions
                  Each filter is a tuple (builtin_name, arg1, arg2, ...)

        Returns:
            LiveQueryResultSet that updates automatically

        Example:
            # Basic live query
            live = r.live_pattern(
                ("?x", "type", "Person"),
                ("?x", "hasAge", "?age")
            )

            print(len(live))  # 10

            r.load_ontology("...")  # Add new person

            print(len(live))  # 11 (auto-updated!)

            # With callback
            def on_update(token, is_addition):
                if is_addition:
                    print(f"Added: {token.get_all_bindings()}")

            live.on_change(on_update)
        """
        import hashlib

        # Auto-generate cache key if not provided
        if cache is None:
            pattern_str = str((patterns, where))
            cache = hashlib.md5(pattern_str.encode()).hexdigest()[:16]

        # Convert triple patterns to Condition objects (same as pattern())
        conditions = []
        variables = set()

        for (subj, pred, obj) in patterns:
            if pred == "type":
                # (?x, type, Person) maps to instance_of facts
                fact_var = f"?f_{len(conditions)}"
                conditions.append(owl_rete_cpp.Condition(fact_var, "type", "instance_of"))
                conditions.append(owl_rete_cpp.Condition(fact_var, "concept", obj))
                conditions.append(owl_rete_cpp.Condition(fact_var, "individual", subj))
                if subj.startswith("?"):
                    variables.add(subj)
            else:
                # (?x, hasAge, ?age) maps to data_assertion facts
                fact_var = f"?f_{len(conditions)}"
                conditions.append(owl_rete_cpp.Condition(fact_var, "type", "data_assertion"))
                conditions.append(owl_rete_cpp.Condition(fact_var, "subject", subj))
                conditions.append(owl_rete_cpp.Condition(fact_var, "property", pred))
                conditions.append(owl_rete_cpp.Condition(fact_var, "value", obj))
                if subj.startswith("?"):
                    variables.add(subj)
                if obj.startswith("?"):
                    variables.add(obj)

        # Build live query
        if where:
            builtin_filters = [list(filter_spec) for filter_spec in where]
            live_query = self.network.build_live_query_with_filters(cache, conditions, builtin_filters)
        else:
            live_query = self.network.build_live_query(cache, conditions)

        return_vars = select if select else sorted(variables)
        return LiveQueryResultSet(live_query, return_vars, self.network)

    def get_all_facts(self):
        """
        Get all facts in the network

        Returns:
            PyArrow Table (zero-copy, supports iteration, indexing, to_pandas())
        """
        # Return Arrow table directly for zero-copy access from Python
        # Python can iterate, index, filter, or convert to pandas without copying
        return self.network.get_all_facts_arrow()

    def get_inferred_facts(self):
        """
        Get only inferred facts

        Returns:
            PyArrow Table with only inferred facts (zero-copy filtered)
        """
        import pyarrow.compute as pc
        all_facts = self.get_all_facts()

        # Use Arrow compute to filter (zero-copy, very fast)
        if 'inferred' in all_facts.column_names:
            mask = pc.equal(all_facts['inferred'], 'true')
            return all_facts.filter(mask)
        else:
            # No 'inferred' column means no inferred facts
            return all_facts.slice(0, 0)  # Empty table with same schema

    def get_instances(self, concept):
        """
        Get all instances of a concept

        Args:
            concept: Concept name

        Returns:
            List of unique individual names (list for backwards compatibility)
        """
        import pyarrow.compute as pc
        all_facts = self.get_all_facts()

        # Filter for instance_of facts with matching concept (zero-copy)
        if 'type' in all_facts.column_names and 'concept' in all_facts.column_names:
            type_mask = pc.equal(all_facts['type'], 'instance_of')
            concept_mask = pc.equal(all_facts['concept'], concept)
            mask = pc.and_(type_mask, concept_mask)
            filtered = all_facts.filter(mask)
        else:
            # Return empty table if columns don't exist
            filtered = all_facts.slice(0, 0)

        # Extract 'individual' column and get unique values
        if 'individual' in filtered.column_names and filtered.num_rows > 0:
            individuals = filtered['individual'].to_pylist()
            return list(set(individuals))  # Remove duplicates
        return []

    def get_subsumers(self, concept):
        """
        Get all subsumers (superclasses) of a concept

        Args:
            concept: Concept name

        Returns:
            List of unique subsumer concept names
        """
        import pyarrow.compute as pc
        all_facts = self.get_all_facts()

        # Filter for subsumption facts with matching sub (zero-copy)
        if 'type' in all_facts.column_names and 'sub' in all_facts.column_names:
            type_mask = pc.equal(all_facts['type'], 'subsumption')
            sub_mask = pc.equal(all_facts['sub'], concept)
            mask = pc.and_(type_mask, sub_mask)
            filtered = all_facts.filter(mask)
        else:
            # Return empty table if columns don't exist
            filtered = all_facts.slice(0, 0)

        # Extract 'sup' column and get unique values
        if 'sup' in filtered.column_names and filtered.num_rows > 0:
            subsumers = filtered['sup'].to_pylist()
            return list(set(subsumers))
        return []

    def get_subsumed(self, concept):
        """
        Get all subsumed concepts (subclasses) of a concept

        Args:
            concept: Concept name

        Returns:
            List of unique subsumed concept names
        """
        import pyarrow.compute as pc
        all_facts = self.get_all_facts()

        # Filter for subsumption facts with matching sup (zero-copy)
        if 'type' in all_facts.column_names and 'sup' in all_facts.column_names:
            type_mask = pc.equal(all_facts['type'], 'subsumption')
            sup_mask = pc.equal(all_facts['sup'], concept)
            mask = pc.and_(type_mask, sup_mask)
            filtered = all_facts.filter(mask)
        else:
            # Return empty table if columns don't exist
            filtered = all_facts.slice(0, 0)

        # Extract 'sub' column and get unique values
        if 'sub' in filtered.column_names and filtered.num_rows > 0:
            subsumed = filtered['sub'].to_pylist()
            return list(set(subsumed))
        return []

    def get_role_assertions(self, role=None, subject=None, object=None):
        """
        Get role assertions matching criteria

        Args:
            role: Role name (optional)
            subject: Subject individual (optional)
            object: Object individual (optional)

        Returns:
            List of (subject, role, object) tuples
        """
        import pyarrow.compute as pc
        all_facts = self.get_all_facts()

        # Build filter mask for role assertions (zero-copy filtering)
        if 'type' not in all_facts.column_names:
            return []

        mask = pc.equal(all_facts['type'], 'role_assertion')

        # Add optional filters
        if role and 'role' in all_facts.column_names:
            role_mask = pc.equal(all_facts['role'], role)
            mask = pc.and_(mask, role_mask)
        if subject and 'subject' in all_facts.column_names:
            subject_mask = pc.equal(all_facts['subject'], subject)
            mask = pc.and_(mask, subject_mask)
        if object and 'object' in all_facts.column_names:
            object_mask = pc.equal(all_facts['object'], object)
            mask = pc.and_(mask, object_mask)

        # Filter the table (zero-copy)
        filtered = all_facts.filter(mask)

        # Extract tuples (subject, role, object)
        if filtered.num_rows > 0:
            if 'subject' in filtered.column_names and 'role' in filtered.column_names and 'object' in filtered.column_names:
                subjects = filtered['subject'].to_pylist()
                roles = filtered['role'].to_pylist()
                objects = filtered['object'].to_pylist()
                return list(zip(subjects, roles, objects))

        return []

    def check_consistency(self):
        """
        Check for inconsistencies in the ontology

        Returns:
            (is_consistent, list_of_inconsistencies)
        """
        inconsistencies = self.query(type='inconsistency')

        if inconsistencies:
            return False, inconsistencies
        else:
            return True, []

    # ========================================================================
    # Source Tracking Methods (Phase 5)
    # ========================================================================

    def remove_source(self, source_id):
        """
        Remove all facts from a source and all derived facts

        Args:
            source_id: Source identifier to remove

        Example:
            r.load_ontology("...", source="ontology1")
            r.remove_source("ontology1")  # Removes ontology1 and derived facts
        """
        self.network.remove_source(source_id)

    def get_all_sources(self):
        """
        Get all source identifiers

        Returns:
            List of source identifier strings

        Example:
            sources = r.get_all_sources()
            print(f"Active sources: {sources}")
        """
        return self.network.get_all_sources()

    def get_facts_from_source(self, source_id):
        """
        Get all fact IDs from a specific source

        Args:
            source_id: Source identifier

        Returns:
            List of fact ID strings

        Example:
            fact_ids = r.get_facts_from_source("ontology1")
            print(f"Facts from ontology1: {len(fact_ids)}")
        """
        return self.network.get_facts_from_source(source_id)

    def print_summary(self):
        """Print summary of the ontology and reasoning results"""
        all_facts = self.get_all_facts()
        inferred_facts = self.get_inferred_facts()

        # Count facts by type
        fact_types = {}
        for fact in all_facts:
            fact_type = fact.get('type', 'unknown')
            fact_types[fact_type] = fact_types.get(fact_type, 0) + 1

        # Check consistency
        is_consistent, inconsistencies = self.check_consistency()

    def export_facts(self, filepath, format='human'):
        """
        Export facts to file

        Args:
            filepath: Output file path
            format: 'human' or 'json'
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            if format == 'human':
                for fact in self.get_all_facts():
                    inferred = " [INFERRED]" if fact.get('inferred') == 'true' else ""
                    f.write(f"{fact}{inferred}\n")
            elif format == 'json':
                import json
                facts_data = self.get_all_facts()
                json.dump(facts_data, f, indent=2)


def main():
    """Example usage"""
    reasoner = Reter()

    # Example ontology (uses Unicode fullwidth parentheses for instances)
    ontology = """
    Person ⊑ᑦ Animal
    Cat ⊑ᑦ Animal
    Student ⊑ᑦ Person
    Person（John）
    Person（Mary）
    Cat（Felix）
    Student（Alice）
    hasParent ⊑ᴿ hasAncestor
    hasParent（John，Mary）
    """

    reasoner.load_ontology(ontology)
    reasoner.reason()
    reasoner.print_summary()

    # Query examples
    animals = reasoner.get_instances('Animal')
    subsumers = reasoner.get_subsumers('Student')


if __name__ == '__main__':
    main()
