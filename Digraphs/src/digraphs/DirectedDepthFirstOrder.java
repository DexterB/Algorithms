package digraphs;

import java.util.Stack;

import sun.misc.Queue;

/**
 * Depth first class which computes and tracks the visitation of nodes in the 
 * digraph in depth-first order.
 * @author dbradsha
 *
 */
public class DirectedDepthFirstOrder {
	boolean [] marked;					// marks nodes already visited
	private Queue<Integer> pre;			// pre order visitation of vertices
	private Queue<Integer> post;		// post order visitation of vertices
	private Stack<Integer> reversePost; // reverse post order visitation of vertices
	
	public DirectedDepthFirstOrder (Digraph G) {
		pre = new Queue<Integer>();
		post = new Queue<Integer>();
		reversePost = new Stack<Integer>();
		
		marked = new boolean [G.V()];
		for (int v = 0; v < G.V(); v++) {
			if (!marked[v]) {
				dfs(G, v);
			}
		}
	}
	
	private void dfs(Digraph G, int v) {
		pre.enqueue(v);
		for (int w : G.adj(v)) {
			if (!marked[w]) {
				marked[w] = true;
				dfs(G, w);
			}
		}
		post.enqueue(v);
		reversePost.push(v);
	}
	
	public Iterable<Integer> pre() {
		return pre;
	}
	
	public Iterable<Integer> post() {
		return post;
	}
	
	public Iterable<Integer> reversePost() {
		return reversePost;
	}
}
