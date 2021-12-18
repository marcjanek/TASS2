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
	pathToFiles := "/home/tomek/Pulpit/pdfs/"
	files, err := ioutil.ReadDir(pathToFiles)
	if err != nil {
		log.Fatal(err)
	}

	pdfs := make([]pdf, 0)
	d := createMap("/home/tomek/Pulpit/odm.txt")
	for _, file := range files {
		text, err := getFile(pathToFiles + file.Name())
		if err != nil {
			log.Fatal(err)
		}

		speeches, date := parseText(text)
		speeches1 := removeSpecialChars(speeches)
		speeches1 = addBaseToWords(speeches1, &d)
		pdf := pdf{
			name:     file.Name(),
			date:     date,
			speeches: speeches1,
		}

		pdfs = append(pdfs, pdf)
	}

	politicians := set{p: map[string]int{}}

	for _, pdf := range pdfs {
		i := 1
		for _, v := range pdf.speeches {
			politicians.add(v.speaker, i)
			i = i + 1
		}
	}

	str := ""
	for politician, id := range politicians.p {
		str = str + insertPolitician(politician, id)
	}

	for _, v := range pdfs {
		str = str + migrateToDatabase(v)
	}
}

func migrateToDatabase(pdfToMigrate pdf) string {
	str := insertDate(pdfToMigrate.date)
	for _, v := range pdfToMigrate.speeches {
		insertStatement(v.speaker, pdfToMigrate.date)
		insertPoliticianWords(v.speaker, v.words, pdfToMigrate.date)
	}

	return str
}

func insertPoliticianWords(speaker string, words []word, date string) string {
	return fmt.Sprintf("")
}

func insertPolitician(speaker string, speakerID int) string {
	split := strings.Split(speaker, " ")
	name := ""
	surname := ""
	if len(split) > 1 {
		name = split[len(split)-2]
		surname = split[len(split)-1]
	} else if len(split) == 1 {
		surname = split[0]
	}

	return fmt.Sprintf("INSERT INTO politicians (id, name, surname) VALUES(%d, %s, %s);\n", speakerID, name, surname)
}

func insertStatement(politicianId string, date string) string {
	return fmt.Sprintf("INSERT INTO statements (politician_id, date) VALUES(%s, %s);\n", politicianId, date)
}

//func insertWord(number string, base string, variety string, statementID int) string {
//	return fmt.Sprintf("INSERT INTO words_list (number, base, variety, statement_id) VALUES (%s, %s, %s, %s);\n", number, base, variety, statementID)
//}

func insertDate(date string) string {
	return fmt.Sprintf("INSERT INTO political_meetings (date) VALUES(%s);\n", date)
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

func removeSpecialChars(speeches []speech) []speechWords {
	speeches1 := make([]speechWords, 0)
	specialChars := regexp.MustCompile("[^A-Za-z0-9ąęóśćżźńłĄĘÓŚĆŻŹŃŁäÄöÖüÜßﬁ]")
	for _, v := range speeches {
		lines := strings.ReplaceAll(v.lines, " - ", " ")
		lines = strings.ReplaceAll(lines, "-", "")
		fmt.Println(specialChars.FindString(lines)) //todo: find all removed words
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

func parseText(pdfText string) ([]speech, string) {
	// nawiasy
	bracketText := regexp.MustCompile("\\([^\\)]*\\)")

	// nagłówki stron
	pageHeaderText := regexp.MustCompile("[0-9][0-9]. posiedzenie Sejmu w dniu")

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
	for i, v := range split { //todo wydobyć date posiedzenia z nagłówka
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

	speeches := make([]speech, 0)
	for i := 0; i < len(indexes)-1; i++ {
		speech := speech{
			speaker: split[indexes[i]],
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
	return append(s[:index], s[index+numberOfLines:]...)
}

func RemoveWord(w []word, index int) []word {
	return append(w[:index], w[index+1:]...)
}

//func removeDuplicateStr(strSlice []string) []string {
//	allKeys := make(map[string]bool)
//	list := []string{}
//	for _, item := range strSlice {
//		if _, value := allKeys[item]; !value {
//			allKeys[item] = true
//			list = append(list, item)
//		}
//	}
//	return list
//}

type set struct {
	p map[string]int
}

func (s *set) add(politician string, id int) {
	if _, ok := s.p[politician]; !ok {
		s.p[politician] = id
	}
}
