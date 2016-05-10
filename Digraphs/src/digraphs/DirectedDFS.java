package digraphs;

import java.util.Stack;

/**
 * Reachability is determined by a depth-first search which marks all vertices
 * that are reachable from a given set of sources in a time proportional to 
 * the sum of the outdegrees of of the vertices marked.
 * 
 * @author dbradsha
 *
 */
public class DirectedDFS {
    private boolean [] marked;
    private int[] edgeTo;
    private int   source;
    private Iterable<Integer> sources = null;
    
    /**
     * Constructor for the  directed depth-first search.
     * @param G is the directed graph.
     * @param s is the single sources
     */
    public DirectedDFS (Digraph G, int s) {
        marked = new boolean [G.V()];
        source = s;
        edgeTo = new int [G.V()];
        dfs(G,s);
    }
    
    /**
     * Constructor for the directed depth-first search.
     * @param G is the directed graph.
     * @param sources is the set of sources
     */
    public DirectedDFS (Digraph G, Iterable<Integer> sources) {
        marked = new boolean [G.V()];
        this.sources = sources;
        for (int s : sources) {
            if(!marked[s]) {
                dfs(G,s);
            }
        }
    }
    
    private void dfs(Digraph G, int v) {
        if (marked[v]) {
            // v was already visited. So return.
            return;
        }
        
        // v was not yet visited. Mark v as visited and visit all the adjacent
        // nodes of v.
        marked [v] = true;
        for (int w : G.adj(v)) {
            if (!marked [w]) {
            	edgeTo[w] = v;
                dfs(G, w);
            }
        }
    }
    
    /**
     * Test if the node was reached.
     * @param v there is a path from the source to vertex, v
     * @return true if the path exists.
     */
    public boolean marked(int v) {
        return marked[v];
    }
    
    /**
     * There is a path from the source to vertex v.
     * @param v is the target vertex
     * @return true if there is a path from the source to the target vertex.
     */
    public boolean hasPathTo(int v) {
    	return marked(v);
    }
    
    /**
     * Determine if the given vertex is in the set of source vertices.
     * @param v is the vertex to be checked on.
     * @return true if v is a source vertex, and false otherwise.
     */
    private boolean isSource(int v) {
    	for (int w : sources) {
    		if (w == v) {
    			return true;
    		}
    	}
    	
    	// Vertex was not found among the sources, return false.
    	return false;
    }
    
    /**
     * Check that the target vertex is reachable from the source.
     * @param G is the digraph
     * @param source is the singleton source vertex
     * @param target is the target node reachable from the source
     * @return true if the target vertex is reachable false otherwise
     */
    public boolean reachable (Digraph G, int source, int target) {
        DirectedDFS R = new DirectedDFS(G, source);
        
        // A node is reachable  if it is marked.
        return R.marked(target);
    }
    
    /**
     * Check that the target vertex is reachable from the set of sources.
     * @param G is the digraph
     * @param sources is a set of source vertices.
     * @param target is the target vertex reachable from any of the sources.
     * @return true if the target vertex is reachable and false otherwise.
     */
    public boolean reachable (Digraph G, Iterable<Integer> sources, int target){
        DirectedDFS R = new DirectedDFS(G, sources);
        
        // The target is reachable only if it is marked in the directedDFS.
        return R.marked(target);
    }
    
    public Iterable<Integer> pathTo (int v) {
    	if (!hasPathTo(v)){
    		// v is not reachable from the source. There is no path.
    		return null;
    	}
    	
    	// There is a path from the source to v
    	Stack<Integer> path = new Stack<Integer>();
    	int n = 0;
    	if (sources == null) {
    		for (n = v; n != source; n = edgeTo[v]) {
    			path.push(n);
    		}
    	} else {
    		for (n = v; !isSource(n); n = edgeTo[v]) {
    			path.push(n);
    		}
    	}
    	
    	// Insert the source onto the path.
    	path.push(n);
    	
    	// Return the path.
    	return path;
    	
    }
}
