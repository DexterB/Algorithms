package digraphs;

public class DirectedTopological {
	private Iterable<Integer> order;
	
	public DirectedTopological(Digraph G) {
		DirectedCycle cycleFinder = new DirectedCycle(G);
		if (!cycleFinder.hasCycle()) {
			DirectedDepthFirstOrder dfs = new DirectedDepthFirstOrder(G);
			order = dfs.reversePost();
		}
	}
	
	public Iterable<Integer> order() {
		return order;
	}
	
	public boolean isDAG() {
		return order = nullo
	}
}
