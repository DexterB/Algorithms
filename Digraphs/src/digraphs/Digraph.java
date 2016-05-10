package digraphs;

import java.util.ArrayList;

/**
 * Digraph class representing the the general digraph data structure.
 * The class consists of the the number of nodes, the number of edges,
 * and the node adjacency list.
 * @author dbradsha
 *
 */
public class Digraph {
	private int V;                     // Number of nodes
	private int E;                     // Number of edges
	private ArrayList<Integer> [] adj; // Node adjacency list
	
	/**
	 * Diagraph constructor.
	 * @param V is the number of nodes in the Digraph.
	 */
	public Digraph (int V) {
	    this.V = V;
	    this.E = 0;
	    
	    adj = (ArrayList<Integer> []) new ArrayList[V];
	    for (ArrayList<Integer> adjList : adj) {
	        adjList = new ArrayList<Integer>();
	    }
	}
	
	/**
	 * Query the number of vertices in the digraph.
	 * @return number of vertices in the digraph.
	 */
	public int V() {
		return V;
	}
	
	/**
	 * Query the number of edges in the digraph.
	 * 
	 * @return number of edges in the digraph.
	 */
	public int E() {
		return E;
	}
	
	/**
	 * Query the adjacency list for a given vertex.
	 * @param v is the target vertex for the adjacency list
	 * @return adjacency list for v.
	 */
	public Iterable<Integer> adj(int v) {
		return adj[v];
	}
	
	/**
	 * Add a directed edge from v to w into the digraph.
	 * @param v is the node at the start of the directed edge.
	 * @param w is the node at the end of the directed edge.
	 */
	public void addEdge(int v, int w) {
	    adj[v].add(w);
	}
	
	/**
     * Create a digraph in which all the directed edges of the graph are
     * reversed.
     * 
	 * @return R, the reversed digraph.
	 */
	public Digraph reverse() {
	    Digraph R = new Digraph(V);
	    for (int v = 0; v < V; v++) {
	        for (int w : adj[v]) {
	            R.addEdge(w, v);
	        }
	    }
	    
	    // Return the reversed Digraph.
	    return R;
	}

}
