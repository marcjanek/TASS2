import os

import networkx as nx
from networkx.algorithms import bipartite
import matplotlib.pyplot as plt
from os import listdir
from os.path import isfile, join
import pyodbc

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

	def draw_all(self):
		for i in self.files:
			if self.files[i].with_friends == 'with_friends':
				self.files[i].draw_circular()
				self.files[i].draw_bipartite()
			else:
				self.files[i].draw_circular()
				self.files[i].draw_bipartite()

	def difference_a_minus_b(self):
		g_a = self.files['after.csv'].g
		g_b = self.files['before.csv'].g
		return self._difference(g_a,
		                        g_b,
		                        './results/' + self.date + '/' + self.interval + '/' + self.friends + '/difference_b_minus_a',
		                        'TODO'
		                        )

	def difference_b_minus_a(self):
		g_a = self.files['after.csv'].g
		g_b = self.files['before.csv'].g
		return self._difference(g_b,
		                        g_a,
		                        './results/' + self.date + '/' + self.interval + '/' + self.friends + '/difference_b_minus_a',
		                        'TODO'
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

		x, y = bipartite.sets(g_new)

		for u,v,d in g_new.edges(data=True):
			d['weight'] = g[u][v]["weight"]-h[u][v]["weight"]

		self.files['after.csv'].draw(g_new, nx.bipartite_layout(g_new, x),
		                             './results/' + self.date + '/' + self.interval + '/' + self.friends + '/intersection',
		                             'TODO')
		return g_new

	def count_words(self):
		g = self.files['after.csv'].g
		h = self.files['before.csv'].g

		y_a = {}
		x, y = bipartite.sets(g)

		for u in y:
			sum = 0
			for e in g.edges(u):
				sum += g[e[0]][e[1]]["weight"]
			y_a[u] = sum

		y_b = {}
		x, y = bipartite.sets(h)

		for u in y:
			sum = 0
			for e in h.edges(u):
				sum += h[e[0]][e[1]]["weight"]
			y_b[u] = sum

		words = {}
		for k in y_b:
			words[k] = [y_b[k], 0]

		for k in y_a:
			if k in words:
				words[k] = [y_b[k], y_a[k]]
			else:
				words[k] = [0, y_a[k]]
		return words


class Graph:
	def __init__(self, date, interval, with_friends, file):
		self.date = date
		self.interval = interval
		self.with_friends = with_friends
		self.file = file

		self.g = self.new_graph()

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

		nx.draw_networkx_edge_labels(g, pos, edge_labels=self.get_edge_attributes('weight', g))
		plt.title(title)
		plt.savefig(out_path)
		plt.show()

	def draw_circular(self):
		self.draw(self.g_x,
		          nx.circular_layout(self.g_x),
		          './results/' + self.date + '/' + self.interval + '/' + self.with_friends + '/' + self.file[
		                                                                                           :-4] + '_circular',
		          'Graf przedstawiający politków ' + self.title()
		          )

	def draw_bipartite(self):
		self.draw(self.g,
		          nx.bipartite_layout(self.g, self.x),
		          './results/' + self.date + '/' + self.interval + '/' + self.with_friends + '/' + self.file[
		                                                                                           :-4] + '_bipartite',
		          'Graf dwudzielny przedstawiający polityków ' + self.title()
		          )

	def get_edge_attributes(self, name, g):
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

		str += ', gdzie '
		str += 'środek bufora to ' + self.date + ', a jego promień wynosi ' + self.interval + 'dni.'

		return str


d = Data()

# d.draw_all()
# d.dates['2021-01-17'].intervals['47'].friends['without_friends'].difference_b_minus_a()
# d.dates['2021-01-17'].intervals['47'].friends['without_friends'].difference_a_minus_b()
d.dates['2021-01-17'].intervals['47'].friends['without_friends'].intersection_graph()
print(d.dates['2021-01-17'].intervals['47'].friends['without_friends'].count_words())

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


print(create_sql('2021-01-17', 47))
