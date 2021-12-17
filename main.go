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

		speeches := parseText(text)
		speeches1 := removeSpecialChars(speeches)
		speeches1 = addBaseToWords(speeches1, &d)
		pdf := pdf{
			name:     file.Name(),
			date:     "",
			speeches: speeches1,
		}

		pdfs = append(pdfs, pdf)
	}
	//for _, v := range pdfs {
	//
	//}
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

func parseText(pdfText string) []speech {
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

	speeches := make([]speech, 0)
	for i := 0; i < len(indexes)-1; i++ {
		speech := speech{
			speaker: split[indexes[i]],
			lines:   strings.Join(split[indexes[i]+1:indexes[i+1]], " "),
		}

		speeches = append(speeches, speech)
	}

	return speeches
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
