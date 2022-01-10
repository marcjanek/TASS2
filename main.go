package main

import (
	"bufio"
	"code.sajari.com/docconv"
	"fmt"
	"io/ioutil"
	"log"
	"os"
	"regexp"
	"strings"
)

type speech struct {
	speaker string
	lines   string
}

type word struct {
	base    string
	variety string
}

type speechWords struct {
	speaker string
	words   []word
}

type pdf struct {
	name     string
	date     string
	speeches []speechWords
}

func main() {
	pathToFiles := "data1/"
	files, err := ioutil.ReadDir(pathToFiles)
	if err != nil {
		log.Fatal(err)
	}

	names := polishNames("./imiona.txt")

	pdfs := make([]pdf, 0)
	d := createMap("odm.txt")
	specialChars := dic{m: map[string]string{}}
	i := 1.0
	for _, file := range files {
		progress := i / 623 * 100
		fmt.Printf("%g ", progress)
		i = i + 1
		fmt.Println(file.Name())
		text, err := getFile(pathToFiles + file.Name())
		if err != nil {
			log.Fatal(err)
		}

		speeches, date := parseText(text, names)
		speeches1 := removeSpecialChars(speeches, &specialChars)
		speeches1 = addBaseToWords(speeches1, &d)
		pdf := pdf{
			name:     file.Name(),
			date:     date,
			speeches: speeches1,
		}

		pdfs = append(pdfs, pdf)
	}

	fmt.Println(specialChars)

	politicians := set{p: map[string]int{}}

	j := 1
	for _, pdf := range pdfs {
		for _, v := range pdf.speeches {
			politicians.add(v.speaker, j)
			j = j + 1
		}
	}

	for politician, id := range politicians.p {
		appendToFile(insertPolitician(politician, id))
	}

	statementID := 1

	for _, v := range pdfs {
		appendToFile(migrateToDatabase(v, &statementID, politicians))
	}
}

func migrateToDatabase(pdfToMigrate pdf, statementID *int, politicians set) string {
	str := insertDate(pdfToMigrate.date)
	for _, v := range pdfToMigrate.speeches {
		str += insertStatement(*statementID, politicians.p[v.speaker], pdfToMigrate.date)
		str += insertPoliticianWords(*statementID, v.words)
		*statementID += 1
	}

	return str
}

func appendToFile(text string) {
	f, err := os.OpenFile("sql.txt",
		os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		log.Println(err)
	}
	defer f.Close()
	if _, err := f.WriteString(text); err != nil {
		log.Println(err)
	}
}

func insertPoliticianWords(statementID int, words []word) string {
	str := "INSERT INTO words_list (number, base, variety, statement_id) VALUES "
	for k, v := range words {
		str += insertWord(k, v.base, v.variety, statementID)
	}
	return str[:len(str)-2] + ";\n"
}

func insertPolitician(speaker string, speakerID int) string {
	return fmt.Sprintf("INSERT INTO politicians (id, name) VALUES(%d, '%s');\n", speakerID, speaker)
}

func insertStatement(id int, politicianId int, date string) string {
	return fmt.Sprintf("INSERT INTO statements (id, politician_id, date) VALUES(%d, %d, '%s');\n", id, politicianId, date)
}

func insertWord(number int, base string, variety string, statementID int) string {
	return fmt.Sprintf("(%d, '%s', '%s', %d), ", number, base, variety, statementID)
}

func insertDate(date string) string {
	return fmt.Sprintf("INSERT INTO political_meetings (date) VALUES('%s');\n", date)
}

type dic struct {
	m map[string]string
}

func (d *dic) add(k, v string) {
	d.m[k] = v
}

func (d *dic) find(key string) string {
	if value, ok := d.m[key]; ok {
		return value
	}

	return key
}

func createMap(path string) dic {
	d := dic{
		m: make(map[string]string, 0),
	}

	f, _ := os.Open(path)
	defer f.Close()

	// Splits on newlines by default.
	s := bufio.NewScanner(f)

	line := 1
	for s.Scan() {
		split := strings.Split(s.Text(), ", ")
		for i := 0; i < len(split); i++ {
			d.add(split[i], split[0])
		}
		line++
	}

	return d
}

func addBaseToWords(speeches []speechWords, d *dic) []speechWords {
	for i := range speeches {
		for i1, v := range speeches[i].words {
			speeches[i].words[i1].base = d.find(v.variety)
		}
	}

	return speeches
}

func removeSpecialChars(speeches []speech, d *dic) []speechWords {
	speeches1 := make([]speechWords, 0)
	badCharsRegex := "[^A-Za-z0-9ąęóśćżźńłĄĘÓŚĆŻŹŃŁäÄöÖüÜéÀµÁÇÉ×àáãåçèêëíîñòôõøùúýăČčėěğįıōőřŞşŠšūůųŽžμЗПабвгдежзийклмнопрстухцчшщьяєії]"
	specialChars := regexp.MustCompile(badCharsRegex)
	toReplace := map[string]string{"ﬁ": "fi", "ﬂ": "fl", "‑": "-", "–": "-", "—": "-", "−": "-", "\u00AD": "-"}
	for _, v := range speeches {
		lines := v.lines
		for k, v := range toReplace {
			lines = strings.ReplaceAll(lines, k, v)
		}
		lines = strings.ReplaceAll(lines, " - ", " ")
		lines = strings.ReplaceAll(lines, "-", "")

		badChars := specialChars.FindAllString(lines, -1)
		for _, v := range badChars {
			d.add(v, "")
		}

		lines = specialChars.ReplaceAllString(lines, " ")

		v.speaker = strings.ReplaceAll(v.speaker, ":", "")

		lines = strings.ToLower(lines)
		split := strings.Split(lines, " ")
		words := make([]word, 0)

		for _, v := range split {
			words = append(words, word{
				base:    "",
				variety: strings.TrimSpace(v),
			})
		}

		for i := len(words) - 1; i >= 0; i-- {
			if words[i].variety == "" {
				words = RemoveWord(words, i)
			}
		}

		speechWord := speechWords{
			speaker: v.speaker,
			words:   words,
		}

		speeches1 = append(speeches1, speechWord)
	}

	return speeches1
}

func getFile(path string) (string, error) {
	res, err := docconv.ConvertPath(path)
	if err != nil {
		return "", err
	}
	return res.Body, nil
}

func parseText(pdfText string, names dic) ([]speech, string) {
	// nawiasy
	bracketText := regexp.MustCompile("\\([^\\)]*\\)")

	// nagłówki stron
	pageHeaderText := regexp.MustCompile("[0-9]?[0-9]. posiedzenie Sejmu w dniu")

	// usuniecie tekstu w nawiasach
	text := strings.ReplaceAll(pdfText, "\n", "!~")
	text = bracketText.ReplaceAllString(text, "")
	text = strings.ReplaceAll(text, "!~", "\n")

	// usuniecie dwukropkow
	text = strings.ReplaceAll(text, ": ", " ")
	text = strings.ReplaceAll(text, ":\n— ", "")

	split := strings.Split(text, "\n")

	// usuniecie naglowkow stron
	indexesToRemove := make([]int, 0)
	for i, v := range split {
		if pageHeaderText.Match([]byte(v)) {
			indexesToRemove = append(indexesToRemove, i)
		}
	}

	date := Date(split[indexesToRemove[0]])

	for i := len(indexesToRemove) - 1; i >= 0; i-- {
		split = Remove(split, indexesToRemove[i], 6)
	}

	//podzial na pojedyncze wypowiedzi
	indexes := make([]int, 0)
	for i, v := range split {
		if strings.Contains(v, ":") {
			indexes = append(indexes, i)
		}
	}

	//sprawdz czy przedostatnie slowo to imie
	for i := len(indexes) - 1; i >= 0; i-- {
		speaker := strings.Split(split[indexes[i]], " ")
		if len(speaker) < 2 {
			if speaker[0] != "Marszałek:" {
				indexes = append(indexes[:i], indexes[i+1:]...)
			}

			continue
		}

		name := speaker[len(speaker)-2]
		if names.find(name) != "" {
			indexes = append(indexes[:i], indexes[i+1:]...)
		}
	}

	speeches := make([]speech, 0)
	for i := 0; i < len(indexes)-1; i++ {
		speaker := strings.Split(split[indexes[i]][:len(split[indexes[i]])-1], " ")
		if len(speaker) < 2 {
			speech := speech{
				speaker: strings.Join(speaker, " "),
				lines:   strings.Join(split[indexes[i]+1:indexes[i+1]], " "),
			}

			speeches = append(speeches, speech)
			continue
		}

		speech := speech{
			speaker: strings.Join(speaker[len(speaker)-2:], " "),
			lines:   strings.Join(split[indexes[i]+1:indexes[i+1]], " "),
		}

		speeches = append(speeches, speech)
	}

	return speeches, date
}

func Date(strDate string) string {
	split := strings.Split(strDate, " ")
	day := split[len(split)-4]
	month := split[len(split)-3]
	year := split[len(split)-2]

	months := map[string]string{
		"stycznia":     "01",
		"lutego":       "02",
		"marca":        "03",
		"kwietnia":     "04",
		"maja":         "05",
		"czerwca":      "06",
		"lipca":        "07",
		"sierpnia":     "08",
		"września":     "09",
		"października": "10",
		"listopada":    "11",
		"grudnia":      "12",
	}

	return fmt.Sprintf("%s-%s-%s", year, months[month], day)
}

func Remove(s []string, index, numberOfLines int) []string {
	if index+numberOfLines > len(s) {
		return s[:index]
	}
	return append(s[:index], s[index+numberOfLines:]...)
}

func RemoveWord(w []word, index int) []word {
	return append(w[:index], w[index+1:]...)
}

type set struct {
	p map[string]int
}

func (s *set) add(politician string, id int) {
	if _, ok := s.p[politician]; !ok {
		s.p[politician] = id
	}
}

func polishNames(path string) dic {
	d := dic{
		m: make(map[string]string, 0),
	}

	f, _ := os.Open(path)
	defer f.Close()

	s := bufio.NewScanner(f)

	for s.Scan() {
		d.add(s.Text(), "")
	}

	return d
}
