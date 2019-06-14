'''
Simple class for working with unweighted undirected graphs
@author: Oleksii Kuchaiev; http://www.kuchaev.com
'''
import random
class graph(object):
    '''
    A class for representing and manipulation undirected, unweighted simple graphs without self-loops
    '''
    def __init__(self, userID=None):
        '''
        Constructor
        '''
        if userID==None:
            self.Id=random.randint(0,10000000)
        else:
            self.Id=userID
        self.Nodes=set() #set of nodes
        self.AdjList=dict() #Adjacency list
    def add_node(self,node):
        '''
        Adds node to the graph.
        '''
        if node in self.Nodes:
            raise Exception("Node "+node+" is already present in the graph.")
        else:
            self.Nodes.add(node)
            self.AdjList[node]=set()
    def add_edge(self,nd1,nd2):
        '''
        Adds edge (nd1,nd2) to the graph.
        '''
        if nd1 not in self.Nodes:
            raise Exception("Node "+nd1+" is not present in the graph.")
        if nd2 not in self.Nodes:
            raise Exception("Node "+nd2+" is not present in the graph.")
        if nd1 not in self.AdjList.keys():
            self.AdjList[nd1]=set()
            self.AdjList[nd1].add(nd2)
        else:
            self.AdjList[nd1].add(nd2)
        if nd2 not in self.AdjList.keys():
            self.AdjList[nd2]=set()
            self.AdjList[nd2].add(nd1)
        else:
            self.AdjList[nd2].add(nd1)                
    def readFromEdgeList(self,path):
        '''
        Read graph from the file where it is represented as an edge list.
        The lines of the file should be formated as:
        node1[space]node2[newline] 
        Duplicate edges and self loops are ignored.
        '''
        inp_file=open(path,'r')
        _Nodes=set() # this will replace self.Nodes in case of success
        _AdjList=dict() # this will replace self.AdjList in case of success        
        for line in inp_file:
            nodes=line.split()
            if len(nodes)<2:
                raise Exception("There is an incorrectly formatted line in the edge list file")
            nd1=nodes[0]
            nd2=nodes[1]
            if nd1==nd2:
                continue
            if (nd1 in _Nodes):
                if (nd2 not in _AdjList[nd1]):
                    _AdjList[nd1].add(nd2)
            else:
                _Nodes.add(nd1)
                _AdjList[nd1]=set()
                _AdjList[nd1].add(nd2)
            if (nd2 in _Nodes):
                if (nd1 not in _AdjList[nd2]):
                    _AdjList[nd2].add(nd1)
            else:
                _Nodes.add(nd2)
                _AdjList[nd2]=set()
                _AdjList[nd2].add(nd1)
        inp_file.close()
        self.Nodes.clear()
        self.AdjList.clear()
        self.Nodes=_Nodes
        self.AdjList=_AdjList
    def get_edge_set(self):
        '''
        Returns set of edges in the graph.        
        '''
        Edges=set()
        for nd1 in self.Nodes:
            N=self.get_node_neighbors(nd1)
            for nd2 in N:
                if (nd2,nd1) not in Edges:
                    Edges.add((nd1,nd2))
        return Edges
    def saveAsEdgeList(self,path):
        '''
        Saves graph as edge list
        '''
        out=open(path,'w')
        EdgeList=self.get_edge_set()
        for edge in EdgeList:
            line = edge[0]+" "+edge[1]+"\n"
            out.write(line)
        out.close()             
    def number_of_nodes(self):
        '''
        Returns number of nodes in the graph.
        '''
        return len(self.Nodes)
    def number_of_edges(self):
        '''
        Returns number of edges in the graph.
        '''
        num_edg=0.0;
        for key in self.AdjList.keys():
            num_edg=num_edg+(float(len(self.AdjList[key]))/2)
        return int(num_edg)    
    def degree(self,node):
        '''
        Returns the degree of a node 
        '''
        if node not in self.Nodes:
            raise Exception("There is no node with name: "+str(node)+" in this graph. The id of the graph is: "+str(self.Id))
        return len(self.AdjList[node])
    def get_node_clust_coef(self,node):
        '''
        Returns the clustering coefficient of the node
        '''
        deg=self.degree(node)
        if deg<=1:
            return 0
        Ev=0
        neighbors=self.get_node_neighbors(node)
        for nd in neighbors:
            if self.are_adjacent(node, nd):
                Ev+=1
        cc=float(2*Ev)/(deg*(deg-1))
        return cc        
    def get_node_eccentricity(self,node):
        '''
        Returns the eccentricity of the node.
        Note that this function returns the eccentricity of a node within its
        connected component
        '''
        D=self.BFS(node)
        ec=0
        for key, value in D:
            if value>ec:
                ec=value
        return ec
    def get_node_eccentricity_avg(self,node):
        '''
        Returns the averaged eccentricity of the node. That is, "avg", not "max" distance
        Note that this function returns the eccentricity of a node within its
        connected component
        '''        
        D=self.BFS(node)
        ec=0.0
        counter=0.0
        for key, value in D.items():
            if value>0:
                ec+=value
                counter+=1
        if counter>0:
            return ec/counter
        else:
            return 0
    def get_node_eccentricities_both(self,node):
        '''
        This function is for performance purposes.
        This is function returns standard and averaged eccentricities of the node.
        Note that both eccentricities of the node are within its connected component
        '''
        D=self.BFS(node)
        ec=0
        ecA=0.0
        counter=0.0
        for key, value in D.items():
            if value>0:
                ecA+=value
                counter+=1
                if value>ec:
                    ec=value
        if counter>0:
            return (ec,ecA/counter)
        else:
            return (ec,0)
    def are_adjacent(self,nd1,nd2):
        '''
        Checks if nd1 and nd2 are connected
        '''
        if nd1 not in self.Nodes:
            raise Exception("Node "+str(nd1)+" is not in the graph with id="+str(self.Id))    
        if nd2 not in self.Nodes:
            raise Exception("Node "+str(nd2)+" is not in the graph with id="+str(self.Id))
        if nd2 in self.AdjList[nd1]:
            return True
        else:
            return False
    def get_node_neighbors(self,nd):
        '''
        Returns set of node neighbors
        '''
        #if nd not in self.Nodes:
           # raise Exception("Node "+str(nd)+" is not in the graph with id="+str(self.Id))
        return self.AdjList[nd]
    def BFS(self,source):
        '''
        Implements Breadth-first search from node 'source' in graph 'self'.
        Returns dictionary D {node: distance from source}
        distance=-1 if 'node' is unreachable from 'source'        
        '''
        #if source not in self.Nodes:
         #   raise Exception("Node "+str(source)+" is not in the graph with id="+str(self.Id))        
        D=dict();
        for node in self.Nodes:
            D[node]=-1
        level=0;
        Que0=set()
        Que0.add(source)
        Que1=set()
        while len(Que0)!=0:
            while len(Que0)!=0:
                cur_node=Que0.pop()
                D[cur_node]=level
                N=self.AdjList[cur_node]
                for nd in N:
                    if D[nd]==-1:
                        Que1.add(nd)                        
            level=level+1
            Que0=Que1
            Que1=set()
        return D
    def dist(self,nd1,nd2):
        '''
        Returns shortest-path distance between nd1 and nd2
        '''
        if nd1 not in self.Nodes:
            raise Exception("Node "+str(nd1)+" is not in the graph with id="+str(self.Id))
        if nd2 not in self.Nodes:
            raise Exception("Node "+str(nd2)+" is not in the graph with id="+str(self.Id))
        D=dict();
        for node in self.Nodes:
            D[node]=-1
        level=0;
        Que0=set()
        Que0.add(nd1)
        Que1=set()
        while len(Que0)!=0:
            while len(Que0)!=0:
                cur_node=Que0.pop()
                D[cur_node]=level
                if cur_node==nd2:
                    return level
                N=self.get_node_neighbors(cur_node)
                for nd in N:
                    if D[nd]==-1:
                        Que1.add(nd)
            level=level+1;
            Que0=Que1;
            Que1=set()
        return -1        
    def all_pairs_dist(self):
        '''
        Returns dictionary of all-pairs shortest paths in 'self'
        The dictionary has format {t=(nd1,nd2): distance},
        where t is a tuple.                
        '''
        Distances=dict()
        count=0
        for nd in self.Nodes:
            DD1=self.BFS(nd)
            for key, value in DD1.items():
                t1=nd, key
                t2=key, nd
                Distances[t1]=float(value)
                Distances[t2]=float(value)
        return Distances
    def find_all_cliques(self):
        '''
        Implements Bron-Kerbosch algorithm, Version 2
        '''
        Cliques=[]
        Stack=[]
        nd=None
        disc_num=len(self.Nodes)
        search_node=(set(),set(self.Nodes),set(),nd,disc_num) 
        Stack.append(search_node)
        while len(Stack)!=0:
            (c_compsub,c_candidates,c_not,c_nd,c_disc_num)=Stack.pop()
            if len(c_candidates)==0 and len(c_not)==0:
                if len(c_compsub)>2:
                    Cliques.append(c_compsub)
                    continue
            for u in list(c_candidates):
                if (c_nd==None) or (not self.are_adjacent(u, c_nd)):
                    c_candidates.remove(u)
                    Nu=self.get_node_neighbors(u)                                
                    new_compsub=set(c_compsub)
                    new_compsub.add(u)
                    new_candidates=set(c_candidates.intersection(Nu))
                    new_not=set(c_not.intersection(Nu))                    
                    if c_nd!=None:
                        if c_nd in new_not:
                            new_disc_num=c_disc_num-1
                            if new_disc_num>0:
                                new_search_node=(new_compsub,new_candidates,new_not,c_nd,new_disc_num)                        
                                Stack.append(new_search_node)
                        else:
                            new_disc_num=len(self.Nodes)
                            new_nd=c_nd
                            for cand_nd in new_not:
                                cand_disc_num=len(new_candidates)-len(new_candidates.intersection(self.get_node_neighbors(cand_nd))) 
                                if cand_disc_num<new_disc_num:
                                    new_disc_num=cand_disc_num
                                    new_nd=cand_nd
                            new_search_node=(new_compsub,new_candidates,new_not,new_nd,new_disc_num)                        
                            Stack.append(new_search_node)                
                    else:
                        new_search_node=(new_compsub,new_candidates,new_not,c_nd,c_disc_num)
                        Stack.append(new_search_node)
                    c_not.add(u) 
                    new_disc_num=0
                    for x in c_candidates:
                        if not self.are_adjacent(x, u):
                            new_disc_num+=1
                    if new_disc_num<c_disc_num and new_disc_num>0:
                        new1_search_node=(c_compsub,c_candidates,c_not,u,new_disc_num)
                        Stack.append(new1_search_node)
                    else:
                        new1_search_node=(c_compsub,c_candidates,c_not,c_nd,c_disc_num)
                        Stack.append(new1_search_node)     
        return Cliques
    def create_empty_graph(self,n):
        '''
        creates graph with n nodes but without edges
        '''
        G=graph()
        for i in range(1,n+1):
            nd=str(i)
            G.add_node(nd)
        return G  
    def create_path_graph(self,n):
        '''
        Create path-graph on n nodes
        '''
        if n<2:
            raise Exception("Can't create a path graph with less than 2 nodes.")
        G=self.create_empty_graph(n)
        for i in range(1,n):
            nd1=str(i)
            nd2=str(i+1)
            G.add_edge(nd1, nd2)
        return G         
    def create_cycle_graph(self,n):
        '''
        Creates graph-cycle on n nodes.
        Nodes are numbered from 1 to n.
        '''
        if n<3:
            raise Exception("Can't create a cycle with less than 3 nodes.") 
        G=self.create_path_graph(n)
        G.add_edge(str(1), str(n))
        return G
    def create_circulant_graph(self,n,j):
        '''
        Creates a circulant graph with n nodes and m edges.
        Nodes are numbered from 1 to n.
        The chords are defined by parameters j.
        That is node i is connected to (i-j) mod n and (i+j) mod n.
        Note that not always the exact match in terms of edges is possible!
        Check the output graph for the number of edges!
        '''
        G=self.create_cycle_graph(n) # node numbers starts from 1         
        for i in range(0,n):
            ndi=str(i % n + 1)
            nd2 = str(( i - j ) % n + 1)
            nd3 = str(( i + j ) % n + 1)
            G.add_edge(ndi, nd2)
            G.add_edge(ndi, nd3)                         
        return G    
    def create_complete_graph(self,n):
        '''
        creates complete graph on n nodes
        '''
        G=self.create_empty_graph(n)
        L=list(G.Nodes)
        for i in range(0,len(L)):
            for j in range(i+1,len(L)):
                G.add_edge(L[i], L[j])
        return G 
             
        
        
        
        
        
        
        
        
        
        
        
        
        
        
            
            