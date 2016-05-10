package digraphs;

import java.util.Stack;

import sun.misc.Queue;

/**
 * For any vertex v reachable from a source s, the breadth-first search (BFS)
 * computes the shortest path from s to v.
 * @author dbradsha
 *
 */
public class DirectedBFS {
	private int[] edgeTo;
	private boolean[] marked;
	private final int source;
	
	/**
	 * Constructor for the DirectedBFs class
	 * @param G is the digraph.
	 * @param source vertex for calculating shortest paths
	 * @throws InterruptedException
	 */
	public DirectedBFS(Digraph G, int source) throws InterruptedException {
		edgeTo = new int [G.V()];
		marked = new boolean [G.V()];
		this.source = source;
		bfs(G, source);
	}
	
	/**
	 * Breadth-first search algorithm queues vertices to be processed. 
	 * @param G is the input digraph
	 * @param s is the source vertex
	 * @throws InterruptedException
	 */
	private void bfs(Digraph G, int s) throws InterruptedException {
		Queue<Integer> queue = new Queue<Integer>();
		marked[s] = true;
		queue.enqueue(s);
		while (!queue.isEmpty()) {
			int v = queue.dequeue();
			for (int w : G.adj(v))
			if (!marked[w]) {
				edgeTo[w] = v;
				marked[w] = true;
				queue.enqueue(w);
			}
		}
	}
	
	/**
	 * Check if there is a path to v.
	 * @param v is the target vertex.
	 * @return true if there is a path from the source to v, false otherwise.
	 */
	public boolean hasPathTo(int v) {
		return marked[v];
	}
	
	/**
	 * Construct the path from the source to the vertex v.
	 * @param v the target vertex v
	 * @return path iterable of integers
	 */
	public Iterable<Integer> pathTo(int v) {
		if (!hasPathTo(v)) {
			return null;
		}
		
		Stack<Integer> path = new Stack<Integer>();
		for (int w = v; w != source; w = edgeTo[w]) {
			path.push(w);
		}
		
		// Push the source on the stack.
		path.push(source);
		
		// Return with the path.
		return path;
	}
}
