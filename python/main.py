import json
import os
from os.path import isfile

import matplotlib.pyplot as plt
import networkx
import networkx as nx
from networkx.algorithms import bipartite

party_id = {
	'Kukiz\'15': 'black',
	'Nowoczesna': 'dodgerblue',
	'PiS': 'darkblue',
	'Wolni i Solidarni': 'darkcyan',
	'PO': 'darkorange',
	'Europejscy Demokraci': 'lime',
	'Republikanie': 'khaki',
	'Liberalno-Społeczni': 'aqua',
	'Przywrócić Prawo': 'lavender',
	'Lewica': 'red',
	'Polska 2050': 'yellow',
	'PSL': 'forestgreen',
	'Konfederacja': 'darkgray',
	'UPR': 'sienna',
	'Polskie Sprawy': 'mediumpurple',
	'Porozumienie': 'violet',
	'PPS': 'darkred',
	'': 'mistyrose'
}


class Data:
	def __init__(self):
		self.dates = {}
		for date in os.listdir('./results'):
			self.dates[date] = Date(date)

	def draw_all(self):
		for i in self.dates:
			self.dates[i].draw_all()

	def get_graph(self, date, interval, with_friends, file):
		return self.dates[date].intervals[interval].friends[with_friends].files[file]


class Date:
	def __init__(self, date):
		self.intervals = {}
		for interval in os.listdir('./results/' + date):
			self.intervals[interval] = Interval(date, interval)

	def draw_all(self):
		for i in self.intervals:
			self.intervals[i].draw_all()


class Interval:
	def __init__(self, date, interval):
		self.friends = {}
		for i in os.listdir('./results/' + date + '/' + interval):
			self.friends[i] = Friends(date, interval, i)

	def draw_all(self):
		for i in self.friends:
			self.friends[i].draw_all()


class Friends:
	def __init__(self, date, interval, friends):
		self.files = {}
		self.date = date
		self.interval = interval
		self.friends = friends
		for file in os.listdir('./results/' + date + '/' + interval + '/' + friends):
			if isfile('./results/' + date + '/' + interval + '/' + friends + '/' + file) and file[-3:] == 'csv':
				self.files[file] = Graph(date, interval, friends, file)
			elif isfile('./results/' + date + '/' + interval + '/' + friends + '/' + file):
				os.remove('./results/' + date + '/' + interval + '/' + friends + '/' + file)

	def draw_all(self):
		self.difference_a_minus_b()
		self.difference_b_minus_a()
		self.intersection_graph()
		for i in self.files:
			self.files[i].draw_circular()
			self.files[i].draw_bipartite()
			self.files[i].betweenness_centrality()
			self.files[i].clustering_coefficient()
			self.files[i].clustering_coefficient_projected()
			print('Modularity, dat: ' + self.files[i].date + ' z interwałem: ' + self.files[i].interval + ' ' +
			      self.files[i].with_friends +
			      ' dla pliku: ' + self.files[i].file +
			      ' wynosi:' + str(self.files[i].modularity()))

	def difference_a_minus_b(self):
		g_a = self.files['after.csv'].g
		g_b = self.files['before.csv'].g
		return self._difference(g_a,
		                        g_b,
		                        './results/' + self.date + '/' + self.interval + '/' + self.friends + '/difference_a_minus_b',
		                        'a-b'
		                        )

	def difference_b_minus_a(self):
		g_a = self.files['after.csv'].g
		g_b = self.files['before.csv'].g
		return self._difference(g_b,
		                        g_a,
		                        './results/' + self.date + '/' + self.interval + '/' + self.friends + '/difference_b_minus_a',
		                        'b-a'
		                        )

	def _difference(self, g, h, out_file, title):
		g_new = g.copy()
		g_new.remove_nodes_from(n for n in g if n in h)

		self.files['after.csv'].draw(g_new, nx.circular_layout(g_new), out_file, title)
		return g_new

	def intersection_graph(self):
		g = self.files['after.csv'].g
		h = self.files['before.csv'].g

		g_new = g.copy()
		g_new.remove_nodes_from(n for n in g if n not in h)
		g_new.remove_edges_from(e for e in g.edges if e not in h.edges)

		g_new = g_new.subgraph(sorted(nx.connected_components(g_new), key=len, reverse=True)[0])
		x, y = bipartite.sets(g_new)

		for u, v, d in g_new.edges(data=True):
			d['weight'] = g[u][v]["weight"] - h[u][v]["weight"]

		self.files['after.csv'].draw(g_new, nx.bipartite_layout(g_new, x),
		                             './results/' + self.date + '/' + self.interval + '/' + self.friends + '/intersection',
		                             'Zmiana w liczbie wypowiedzianych słów, data: ' + self.date)
		return g_new


class Graph:
	def __init__(self, date, interval, with_friends, file):
		self.date = date
		self.interval = interval
		self.with_friends = with_friends
		self.file = file

		self.g = self.new_graph()
		self.g = self.g.subgraph(sorted(nx.connected_components(self.g), key=len, reverse=True)[0])
		self.x, self.y = bipartite.sets(self.g)
		self.g_x = bipartite.weighted_projected_graph(self.g, nodes=list(self.x), ratio=False)
		self.g_y = bipartite.weighted_projected_graph(self.g, nodes=list(self.y), ratio=False)

	def __str__(self):
		return 'results/' + self.date + '/' + self.interval + '/' + self.with_friends + '/' + self.file

	def new_graph(self):
		edges = ""
		party_color = {}
		with open(self.__str__()) as file:
			for line in file:
				s = line[:-1]
				s = s.split(',')
				party_color[s[0]] = party_id[s[-1]]
				party_color[s[1]] = 'white'
				edges += ','.join(s[:-1]) + '\n'

		with open("temp.txt", "w") as text_file:
			text_file.write(edges)

		g = nx.read_weighted_edgelist("temp.txt", delimiter=',', create_using=nx.Graph)
		nx.set_node_attributes(g, party_color, 'Party')

		# nx.set_node_attributes()
		return g

	def draw(self, g, layout, out_path, title):
		nodes = g.nodes()
		colors = [g.nodes[n]['Party'] for n in nodes]
		pos = layout
		plt.figure(3, figsize=(15, 15))

		nx.draw_networkx_nodes(g, pos, nodelist=nodes, node_color=colors)
		nx.draw_networkx_labels(g, pos)
		nx.draw_networkx_edges(g, pos)
		if len(g.nodes) < 30:
			nx.draw_networkx_edge_labels(g, pos, edge_labels=self._get_edge_attributes('weight', g))
		plt.title(title)
		plt.savefig(out_path)
		plt.clf()

		# plt.show()

	def draw_circular(self):
		self.draw(self.g_x,
		          nx.circular_layout(self.g_x),
		          self.out_path() + '_circular',
		          'Sieć politków ' + self.title()
		          )

	def draw_bipartite(self):
		self.draw(self.g,
		          nx.bipartite_layout(self.g, self.x),
		          self.out_path() + '_bipartite',
		          'Sieć dwudzielna polityków ' + self.title()
		          )

	def _get_edge_attributes(self, name, g):
		e = g.edges(data=True)
		return dict((x[:-1], x[-1][name]) for x in e if name in x[-1])

	def title(self):
		str = ''

		if self.file == 'after.csv':
			str += ' po zmianie partii '
		else:
			str += ' przed zmianą partii '

		if self.with_friends == 'with_friends':
			str += 'razem z kolegami partyjnymi '
		else:
			str += 'bez kolegów partyjych '

		str += 'data: ' + self.date + ', promień bufora: ' + self.interval + 'dni.'

		return str

	def betweenness_centrality(self):
		g_new = self.g.copy()

		betweenness = bipartite.betweenness_centrality(g_new, list(self.x))
		nx.set_node_attributes(g_new, betweenness, 'betweenness')

		self.save_to_file('betweenness',
		                  json.dumps(dict(sorted(betweenness.items(), key=lambda item: item[1])), indent=6))

		self.draw1(g_new,
		           nx.bipartite_layout(g_new, self.x),
		           self.out_path() + '_betweenness_centrality',
		           'betweenness centrality',
		           'betweenness'
		           )

	def clustering_coefficient(self):
		g_new = self.g.copy()

		clustering = bipartite.clustering(g_new)
		nx.set_node_attributes(g_new, clustering, 'clustering_coefficient')

		self.save_to_file('clustering_coefficient',
		                  json.dumps(dict(sorted(clustering.items(), key=lambda item: item[1])), indent=6))

		self.draw1(g_new,
		           nx.bipartite_layout(g_new, self.x),
		           self.out_path() + '_clustering_coefficient',
		           'clustering coefficient przed zmianami partyjnymi,' + ' data: ' + self.date + ', promień bufora: ' + self.interval + 'dni.',
		           'clustering_coefficient'
		           )

	def clustering_coefficient_projected(self):
		g_new = self.g_x.copy()

		clustering = nx.clustering(g_new, weight='weight')
		nx.set_node_attributes(g_new, clustering, 'clustering_coefficient_projected')

		self.draw1(g_new,
		           nx.circular_layout(g_new),
		           self.out_path() + '_clustering_coefficient_projected',
		           'clustering coefficient po zmianach partyjnych,' + ' data: ' + self.date + ', promień bufora: ' + self.interval + 'dni.',
		           'clustering_coefficient_projected'
		           )

	def modularity(self):
		g_new = self.g_x.copy()

		party_people = {}

		for node in g_new.nodes():
			c = g_new.nodes[node]['Party']
			if c not in party_people:
				party_people[c] = [node]
			else:
				party_people[c].append(node)

		return networkx.algorithms.community.quality.modularity(g_new, communities=list(party_people.values()),
		                                                        weight='weight')

	def draw1(self, g, pos, out_path, title, attribute):
		nodes = g.nodes()
		colors = [nodes[n][attribute] for n in nodes]

		plt.figure(3, figsize=(15, 15))

		nc = nx.draw_networkx_nodes(g, pos, nodelist=nodes, node_color=colors, vmin=min(colors), vmax=max(colors))
		nx.draw_networkx_labels(g, pos)
		nx.draw_networkx_edges(g, pos)
		if len(g.nodes) < 30:
			nx.draw_networkx_edge_labels(g, pos, edge_labels=self._get_edge_attributes('weight', g))
		plt.title(title)

		cb = plt.colorbar(nc)
		plt.axis('off')

		plt.savefig(out_path)
		plt.clf()
		# plt.show()

	def out_path(self):
		return './results/' + self.date + '/' + self.interval + '/' + self.with_friends + '/' + self.file[:-4]

	def save_to_file(self, suffix, txt):
		f = open(self.out_path() + '_' + suffix + '.txt', 'w')
		f.write(txt)
		f.close()


d = Data()
d.draw_all()

# d.dates['2020-12-09'].draw_all()

# print(d.dates['2021-01-17'].intervals['47'].friends['without_friends'].files['after.csv'].modularity())
# print(d.dates['2021-01-17'].intervals['47'].friends['without_friends'].count_words())

# gr = d.get_graph('2018-12-05', '47', 'without_friends', 'after.csv')
# gr.draw_circular()
# gr.draw_bipartite()

def create_sql(date, interval):
	return f'''-- słowa w nowej partii po base
select name, cw.base, count(cw.base) as xd, p.new_party
from (select p.id, p.name, ppc.new_party
      from politicians p
               join political_parties_changes ppc on p.id = ppc.politician_id
      where abs(date('{date}') - ppc.date) < {interval}
      group by p.id, p.name, ppc.new_party) as p
         join (select s.politician_id, s.id
               from statements s
               where (s.date - date('{date}')) >= {interval} and (s.date - date('{date}')) <= 365 + {interval}) s on p.id = s.politician_id
         join words_list wl on s.id = wl.statement_id
         join chosen_words cw on cw.base = wl.base
group by name, cw.base, p.new_party;

-- słowa w starej partii po base
select name, cw.base, count(cw.base) as xd, p.old_party
from (select p.id, p.name, ppc.old_party
      from politicians p
               join political_parties_changes ppc on p.id = ppc.politician_id
      where abs(date('{date}') - ppc.date) < {interval}
      group by p.id, p.name, ppc.old_party) as p
         join (select s.politician_id, s.id
               from statements s
               where (date('{date}') - s.date) >= {interval} and (date('{date}') - s.date) <= 365 + {interval}) s on p.id = s.politician_id
         join words_list wl on s.id = wl.statement_id
         join chosen_words cw on cw.base = wl.base
group by name, cw.base, p.old_party;

-- koledzy po starej
select p.name, cw.base, count(cw.base) as xd, p.party
from (select p.id, party as party, name
            from (select id, party, name
                  from politicians
                  except
                  select p.id, party, name
                  from politicians p
                           join political_parties_changes ppc on p.id = ppc.politician_id
                  where abs(date('{date}') - ppc.date) < {interval}) p
            where party in (
                select distinct(ppc.old_party)
                from politicians p
                         join political_parties_changes ppc on p.id = ppc.politician_id
                where abs(date('{date}') - ppc.date) < {interval} and ppc.old_party is not null)
            union
            select p.id, ppc.old_party as party, name
            from politicians p
                     join political_parties_changes ppc on p.id = ppc.politician_id
            where abs(date('{date}') - ppc.date) < {interval}) as p
         join (select s.politician_id, s.id
               from statements s
               where (date('{date}') - s.date) >= {interval} and (date('{date}') - s.date) <= 365 + {interval}) s on p.id = s.politician_id
         join words_list wl on s.id = wl.statement_id
         join chosen_words cw on cw.base = wl.base
group by p.name, cw.base, p.party;

-- koledzy po nowej
select p.name, cw.base, count(cw.base) as xd, p.party
from (select p.id, party as party, name
            from (select id, party, name
                  from politicians
                  except
                  select p.id, party, name
                  from politicians p
                           join political_parties_changes ppc on p.id = ppc.politician_id
                  where abs(date('{date}') - ppc.date) < {interval}) p
            where party in (
                select distinct(ppc.new_party)
                from politicians p
                         join political_parties_changes ppc on p.id = ppc.politician_id
                where abs(date('{date}') - ppc.date) < {interval} and ppc.new_party is not null)
            union
            select p.id, ppc.new_party as party, name
            from politicians p
                     join political_parties_changes ppc on p.id = ppc.politician_id
            where abs(date('{date}') - ppc.date) < {interval}) as p
         join (select s.politician_id, s.id
               from statements s
               where (s.date - date('{date}')) >= {interval} and (s.date - date('{date}')) <= 365 + {interval}) s on p.id = s.politician_id
         join words_list wl on s.id = wl.statement_id
         join chosen_words cw on cw.base = wl.base
group by p.name, cw.base, p.party;'''


print(create_sql('2020-12-09', 200))
# Modularity, dat: 2021-01-17 z interwałem: 47 without_friends dla pliku: before.csv wynosi:-0.0619253650621958
# Modularity, dat: 2021-01-17 z interwałem: 47 without_friends dla pliku: after.csv wynosi:-0.15000000000000002
# Modularity, dat: 2021-01-17 z interwałem: 47 with_friends dla pliku: before.csv wynosi:-0.003251178851068709
# Modularity, dat: 2021-01-17 z interwałem: 47 with_friends dla pliku: after.csv wynosi:-0.03287353722652497
# Modularity, dat: 2017-10-11 z interwałem: 100 without_friends dla pliku: before.csv wynosi:-0.09833795013850413
# Modularity, dat: 2017-10-11 z interwałem: 100 without_friends dla pliku: after.csv wynosi:-0.06521114622234991
# Modularity, dat: 2017-10-11 z interwałem: 100 with_friends dla pliku: before.csv wynosi:-0.0009154099047128195
# Modularity, dat: 2017-10-11 z interwałem: 100 with_friends dla pliku: after.csv wynosi:-0.001066757184970959
# Modularity, dat: 2017-10-11 z interwałem: 200 without_friends dla pliku: before.csv wynosi:-0.044927679158448405
# Modularity, dat: 2017-10-11 z interwałem: 200 without_friends dla pliku: after.csv wynosi:-0.061423153871420486
# Modularity, dat: 2017-10-11 z interwałem: 200 with_friends dla pliku: before.csv wynosi:0.00010467127271685217
# Modularity, dat: 2017-10-11 z interwałem: 200 with_friends dla pliku: after.csv wynosi:-0.0012009369252255074
# Modularity, dat: 2020-12-09 z interwałem: 100 without_friends dla pliku: before.csv wynosi:-0.08210526315789472
# Modularity, dat: 2020-12-09 z interwałem: 100 without_friends dla pliku: after.csv wynosi:-0.12521701388888887
# Modularity, dat: 2020-12-09 z interwałem: 100 with_friends dla pliku: before.csv wynosi:0.0019442674593612404
# Modularity, dat: 2020-12-09 z interwałem: 100 with_friends dla pliku: after.csv wynosi:-0.052129734765772845
# Modularity, dat: 2020-12-09 z interwałem: 200 without_friends dla pliku: before.csv wynosi:-0.05660595702255693
# Modularity, dat: 2020-12-09 z interwałem: 200 without_friends dla pliku: after.csv wynosi:-0.06267561983471077
# Modularity, dat: 2020-12-09 z interwałem: 200 with_friends dla pliku: before.csv wynosi:0.0001850091990816217
# Modularity, dat: 2020-12-09 z interwałem: 200 with_friends dla pliku: after.csv wynosi:-0.018350971393228842