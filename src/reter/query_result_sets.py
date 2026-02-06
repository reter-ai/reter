"""
Query Result Set Classes for RETER

Contains wrapper classes for query results from the C++ RETE network:
- QueryResultSet: Basic query result wrapper
- FilteredQueryResultSet: NOT EXISTS filtering
- UnionQueryResultSet: UNION of multiple queries
- PropertyPathResultSet: Transitive closure traversal
- LiveQueryResultSet: Auto-updating query results
"""

# Import C++ RETE implementation from reter_core
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

    ::: This is-in-layer Core-Layer.
    ::: This is a data-transfer-object.
    ::: This is-in-process Main-Process.
    ::: This is stateful.
    ::: This is serializable.
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

        # Get cache key for binding extraction
        # For template queries, _production is already the cache key string
        if isinstance(self._production, str):
            cache_key = self._production
        else:
            cache_key = self._production.cache_key()

        for token in tokens:
            # Extract bindings using cache key (fast path via cached field indices)
            bindings = self._network.extract_bindings(cache_key, token)

            # Return only requested variables (if specified)
            if self._variables:
                yield {v: bindings.get(v, None) for v in self._variables}
            else:
                yield bindings

    def __len__(self):
        """Number of results (requires iteration or Arrow table)"""
        if self._tokens is not None:
            return len(self._tokens)
        # For template queries, _production is a string (cache key), not a production object
        if isinstance(self._production, str):
            # No production object, must count via iteration
            return sum(1 for _ in self)
        return self._production.get_token_count()

    def __getitem__(self, key):
        """
        Support indexed access and slicing:
        - results[0]: First result
        - results[-1]: Last result
        - results[5:10]: Slice of results
        """
        # Materialize if not already done
        if self._arrow_table is None:
            self._materialize()

        # Handle slicing
        if isinstance(key, slice):
            # Convert PyArrow table slice to list of dicts
            sliced = self._arrow_table.slice(
                key.start or 0,
                key.stop - (key.start or 0) if key.stop else None
            )
            return sliced.to_pylist()

        # Handle negative index
        if key < 0:
            key = len(self) + key

        # Single element access
        if key < 0 or key >= len(self):
            raise IndexError(f"Index {key} out of range")

        row = self._arrow_table.slice(key, 1)
        return row.to_pylist()[0]

    def _materialize(self):
        """Materialize results to Arrow table for indexed access"""
        if self._arrow_table is None:
            self._arrow_table = self.to_arrow()

    def __repr__(self):
        count = len(self)
        return f"QueryResultSet({count} results, variables={self._variables})"

    def to_list(self):
        """
        Convert to list of dicts (materializes all results)

        Returns:
            List[Dict[str, Any]]: List of result bindings
        """
        return list(self)

    def to_arrow(self):
        """
        Convert to PyArrow Table (Week 2, Day 6-7: Arrow Integration)
        Uses zero-copy where possible for efficient memory usage.

        Returns:
            pyarrow.Table: Arrow table with results
        """
        try:
            import pyarrow as pa
        except ImportError:
            raise ImportError("pyarrow is required for to_arrow(). Install with: pip install pyarrow")

        # For template queries with cached tokens, build Arrow table from iteration
        if self._tokens is not None or isinstance(self._production, str):
            # Build Arrow table from Python iteration
            results = list(self)
            if not results:
                # Empty table with correct schema
                return pa.table({var: [] for var in self._variables})
            # Convert list of dicts to columnar format
            columns = {var: [r.get(var) for r in results] for var in self._variables}
            return pa.table(columns)

        # Use C++ vectorized to_arrow method for regular queries
        return self._network.query_to_arrow(self._production, self._variables)

    def to_pandas(self):
        """
        Convert to pandas DataFrame (Week 2, Day 1-5)
        Now uses Arrow Table as intermediate for efficiency.

        Returns:
            pandas.DataFrame: DataFrame with query results
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas is required for to_pandas(). Install with: pip install pandas")

        # Use Arrow Table for efficient conversion
        arrow_table = self.to_arrow()

        # Zero-copy conversion where possible
        df = arrow_table.to_pandas()

        # Ensure columns are in the order of variables (if specified)
        if self._variables:
            df = df[self._variables]

        return df


# Check if C++ QueryResultSet is available (Arrow support enabled in reter_core)
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

    ::: This is-in-layer Core-Layer.
    ::: This is a wrapper.
    ::: This is a public-application-programming-interface.
    ::: This is-in-process Main-Process.
    ::: This is stateful.
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

    ::: This is-in-layer Core-Layer.
    ::: This is a data-transformer.
    ::: This is-in-process Main-Process.
    ::: This is stateful.
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

    ::: This is-in-layer Core-Layer.
    ::: This is a query-executor.
    ::: This is-in-process Main-Process.
    ::: This is stateful.
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

    ::: This is-in-layer Core-Layer.
    ::: This is a observer.
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


# Re-export MergedQueryResultSet for backward compatibility
__all__ = [
    "QueryResultSet",
    "MergedQueryResultSet",
    "FilteredQueryResultSet",
    "UnionQueryResultSet",
    "PropertyPathResultSet",
    "LiveQueryResultSet",
]
