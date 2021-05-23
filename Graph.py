from math import inf as infinity



class Graph:
    def __init__(self, connections_matrix:list, nodes:list, weights:list):
        self.connections_matrix = connections_matrix
        self.nodes = nodes
        self.weights = weights

    def _get_index(self, node) -> int:
        '''returns -1 if not found'''
        if isinstance(node,str):
            try:
                return self.nodes.index(node)
            except:
                return -1
        elif isinstance(node,int):
            return node
        else:
            return -1

    def _get_node_name(self, index:int) -> str:
        return self.nodes[index]

    def get_neighbours(self, node) -> list:
        '''returns all neighbours'''
        to_return = []
        index = self._get_index(node)
        if index == -1:
            return to_return

        for neighbour_index in range(len(self.connections_matrix[index])):
            neighbour = self.connections_matrix[index][neighbour_index]
            if neighbour != 0:
                to_return.append(neighbour_index)
        return to_return

    def get_reachable_neighbours(self, node) -> list:
        to_return = []
        index = self._get_index(node)
        if index == -1:
            return to_return

        for neighbour_index in range(len(self.connections_matrix[index])):
            neighbour = self.connections_matrix[index][neighbour_index]
            if neighbour == 1 or neighbour == 3:
                to_return.append(neighbour_index)
        return to_return

    def get_reached_by_neighbours(self, node) -> list:
        to_return = []
        index = self._get_index(node)
        if index == -1:
            return to_return

        for neighbour_index in range(len(self.connections_matrix[index])):
            neighbour = self.connections_matrix[index][neighbour_index]
            if neighbour == 2 or neighbour == 3:
                to_return.append(neighbour_index)
        return to_return
    
    def find_shortest_sending_rout(self, start, end) -> list:
        '''
        find rout between start and end, 
            but start is sender and end is receiver

        returns rout in format [node1, node2, node3], 
            where node1 -> node2 -> node3

        returns empty list if no correlation
        '''

        if isinstance(start,str) and isinstance(end,str):
            try:
                start_index = self.nodes.index(start)
                end_index = self.nodes.index(end)
            except:
                return to_return
        else:
            start_index = start
            end_index = end
        
        if len(self.get_reachable_neighbours(start_index)) == 0\
            or len(self.get_reached_by_neighbours(end_index)) == 0:
            return []


        processed_nodes = {}

        distances = {}
        for node in range(len(self.nodes)):
            distances[node] = infinity
        distances[start_index] = 0

        cannot_be_reached = False

        copy_start = start_index
        while copy_start != end_index:

            processed_nodes[copy_start] = True

            cannot_be_reached = True
            neighbours = self.get_reachable_neighbours(copy_start)
            for neighbour in neighbours:
                if neighbour in processed_nodes:
                    continue
                cannot_be_reached = False
                if distances[neighbour] > distances[copy_start] + 1:
                    distances[neighbour] = distances[copy_start] + 1
            
            if cannot_be_reached:               
                neighbours = self.get_reached_by_neighbours(copy_start)
                for neighbour in neighbours:
                    if distances[copy_start]-1 == distances[neighbour]:
                        copy_start = neighbour
                        break

            else:
                for neighbour in neighbours:
                    if neighbour not in processed_nodes:
                        copy_start = neighbour
                        break

        processed_nodes = {}

        rout = []
        
        copy_end = end_index
        while True:
            processed_nodes[copy_end] = True
            neighbours = self.get_reached_by_neighbours(copy_end)
            
            cannot_be_reached = True
            for neighbour in neighbours:
                if neighbour in processed_nodes:
                    continue

                if distances[copy_end]-1 == distances[neighbour]:
                    rout.insert(0,copy_end)
                    cannot_be_reached = False
                    copy_end = neighbour
                    break
            
            if cannot_be_reached:
                neighbours = self.get_reachable_neighbours(copy_end)
                for neighbour in neighbours:
                    if distances[copy_end] + 1 == distances[neighbour]:
                        copy_end = neighbour
                        break
            if copy_end == start_index:
                rout.insert(0,start_index)
                break
        
        to_return = []
        for node in rout:
            to_return.append(self._get_node_name(node))
        
        return to_return

    def find_strongest_correlations(self, start, end):
        if isinstance(start,str) and isinstance(end,str):
            try:
                start_index = self.nodes.index(start)
                end_index = self.nodes.index(end)
            except:
                return to_return
        else:
            start_index = start
            end_index = end

        processed_nodes = {}

        distances = {}
        for node in range(len(self.nodes)):
            distances[node] = 0
        distances[start_index] = 1

        for node_index in range(len(self.nodes)):
            max_weight = 0
            index_max = -1

            for i in range(len(self.nodes)):
                if i not in processed_nodes\
                   and distances[i] > max_weight:

                    max_weight = distances[i]
                    index_max = i
            processed_nodes[node_index] = True
            for i in range(len(self.nodes)):
                if i in processed_nodes:
                    continue
                if distances[index_max] + self.weights[index_max][i] > distances[i]:
                    distances[i] = distances[index_max] + self.weights[index_max][i]
            

        processed_nodes = {}
        rout = []
        
        copy_end = end_index
        while True:
            processed_nodes[copy_end] = True
            neighbours = self.get_neighbours(copy_end)
            
            for neighbour in neighbours:
                if neighbour in processed_nodes:
                    continue

                if distances[copy_end] - self.weights[copy_end][neighbour] == distances[neighbour]:
                    rout.insert(0,copy_end)
                    copy_end = neighbour
                    break
            
            if copy_end == start_index:
                rout.insert(0,start_index)
                break
        

        

        




