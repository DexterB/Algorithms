package digraphs;

/**
 * The DirectedDepthFirstOrder of an acyclic Digraph returns a topological order
 * for a DAG.
 * 
 * @author dbradsha
 *
 */
public class DirectedTopological {
	private Iterable<Integer> order;
	
	/**
	 * Calculate the topological sort of an acyclic DAG.  A topological sort
	 * is the reverse post-order of any acyclic DAG.
	 * 
	 * @param G input Digraph
	 */
	public DirectedTopological(Digraph G) {
		DirectedCycle cycleFinder = new DirectedCycle(G);
		if (!cycleFinder.hasCycle()) {
			DirectedDepthFirstOrder dfs = new DirectedDepthFirstOrder(G);
			order = dfs.reversePost();
		}
	}
	
	/**
	 * Query the value of the order of the digraph.
	 * @return reverse post order if the DAG is acyclic and null otherwise.
	 */
	public Iterable<Integer> order() {
		return order;
	}
	
	/**
	 * Query whether the directed graph is acyclic.
	 * @return true if the graph is acyclic and false otherwise.
	 */
	public boolean isDAG() {
		return order == null;
	}
}
