package Digraphs;

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
    
    /**
     * Constructor for the  directed depth-first search.
     * @param G is the directed graph.
     * @param s is the single sources
     */
    public DirectedDFS (Digraph G, int s) {
        marked = new boolean [G.V()];
        dfs(G,s);
    }
    
    /**
     * Constructor for the directed depth-first search.
     * @param G is the directed graph.
     * @param sources is the set of sources
     */
    public DirectedDFS (Digraph G, Iterable<Integer> sources) {
        marked = new boolean [G.V()];
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
                dfs(G, w);
            }
        }
    }
    
    /**
     * Test if the node was reached.
     * @param v
     * @return
     */
    public boolean marked(int v) {
        return marked[v];
    }
    
    /**
     * 
     * @param G
     * @param source
     * @param target
     * @return
     */
    public boolean reachable (Digraph G, int source, int target) {
        DirectedDFS R = new DirectedDFS(G, source);
        
        // A node is reachable  if it is marked.
        return R.marked(target);
    }
    
    public boolean reachable (Digraph G, Iterable<Integer> sources, int target){
        DirectedDFS R = new DirectedDFS(G, sources);
        
        // The target is reachable only if it is marked in the directedDFS.
        return R.marked(target);
    }
}
