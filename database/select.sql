-- słowa w nowej partii po base
select name, cw.base, count(cw.base) as xd, p.new_party
from (select p.id, p.name, ppc.new_party
      from politicians p
               join political_parties_changes ppc on p.id = ppc.politician_id
      where abs(date('2017-10-11') - ppc.date) < 200
      group by p.id, p.name, ppc.new_party) as p
         join (select s.politician_id, s.id
               from statements s
               where (s.date - date ('2017-10-11')) >= 200 and (s.date - date('2017-10-11')) <= 365 + 200) s
on p.id = s.politician_id
    join words_list wl on s.id = wl.statement_id
    join chosen_words cw on cw.base = wl.base
group by name, cw.base, p.new_party;

-- słowa w starej partii po base
select name, cw.base, count(cw.base) as xd, p.old_party
from (select p.id, p.name, ppc.old_party
      from politicians p
               join political_parties_changes ppc on p.id = ppc.politician_id
      where abs(date('2017-10-11') - ppc.date) < 200
      group by p.id, p.name, ppc.old_party) as p
         join (select s.politician_id, s.id
               from statements s
               where (date ('2017-10-11') - s.date) >= 200
                 and (date ('2017-10-11') - s.date) <= 365 + 200) s on p.id = s.politician_id
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
            where abs(date('2017-10-11') - ppc.date) < 200) p
      where party in (
          select distinct(ppc.old_party)
          from politicians p
                   join political_parties_changes ppc on p.id = ppc.politician_id
          where abs(date('2017-10-11') - ppc.date) < 200
            and ppc.old_party is not null)
      union
      select p.id, ppc.old_party as party, name
      from politicians p
               join political_parties_changes ppc on p.id = ppc.politician_id
      where abs(date('2017-10-11') - ppc.date) < 200) as p
         join (select s.politician_id, s.id
               from statements s
               where (date ('2017-10-11') - s.date) >= 200
                 and (date ('2017-10-11') - s.date) <= 365 + 200) s on p.id = s.politician_id
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
            where abs(date('2017-10-11') - ppc.date) < 200) p
      where party in (
          select distinct(ppc.new_party)
          from politicians p
                   join political_parties_changes ppc on p.id = ppc.politician_id
          where abs(date('2017-10-11') - ppc.date) < 200
            and ppc.new_party is not null)
      union
      select p.id, ppc.new_party as party, name
      from politicians p
               join political_parties_changes ppc on p.id = ppc.politician_id
      where abs(date('2017-10-11') - ppc.date) < 200) as p
         join (select s.politician_id, s.id
               from statements s
               where (s.date - date ('2017-10-11')) >= 200 and (s.date - date('2017-10-11')) <= 365 + 200) s
on p.id = s.politician_id
    join words_list wl on s.id = wl.statement_id
    join chosen_words cw on cw.base = wl.base
group by p.name, cw.base, p.party;