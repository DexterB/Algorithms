package digraphs;

import java.util.Stack;

/**
 * Implementation of the class to detect and compute cycles in a 
 * directed graph.
 * @author dbradsha
 *
 */
public class DirectedCycle {
	private boolean [] onStack;
	private boolean [] marked;
	private int     [] edgeTo;
	private Stack<Integer> cycle;
	
	/**
	 * Constructor for the DirectedCycle class.
	 * @param G is the digraph to examine for cycles.
	 */
	public DirectedCycle(Digraph G) {
		onStack = new boolean [G.V()];
		marked  = new boolean [G.V()];
		edgeTo  = new int [G.V()];
		cycle   = null;
		
		for (int v = 0; v < G.V(); v++) {
			if (!marked[v]) {
				dfs(G, v);
			}
		}
	}
	
	/**
	 * Depth-first search to probe for cycles in the digraph.
	 * @param G the digraph
	 * @param v source node for detecting cycles in the digraph.
	 */
	private void dfs(Digraph G, int v) {
		onStack[v] = true;
		marked[v]  = true;
		for (int w : G.adj(v)) {
			if (hasCycle()) {
				return;
			}
			
			if (!marked[w]) {
				edgeTo[w] = v;
				dfs(G, w);
			} else if (onStack[w]) {
				cycle = new Stack<Integer>();
				for (int x = v; x != w; x = edgeTo[x]) {
					cycle.push(x);
				}
				cycle.push(w);
				cycle.push(v);
			}
		}
		onStack[v] = false;
	}
	
	/**
	 * Check if a cycle has been already detected in the digraph.
	 * @return true if a cycle has been detected and false otherwise.
	 */
	public boolean hasCycle() {
		return cycle != null;
	}
	
	/**
	 * Enumeration of vertices in any detected cycles.
	 * @return iterable set of vertices in cycle or null if there are no cycles.
	 */
	public Iterable<Integer> cycle() {
		return this.cycle();
	}
}
