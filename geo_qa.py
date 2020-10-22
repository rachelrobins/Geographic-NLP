import requests
import lxml.html
import rdflib
import sys
import re
from rdflib import Literal, XSD

url = "https://en.wikipedia.org"

list_yea = list()

def create_ontology(link,string):
    graph = rdflib.Graph()
    countries_lists = list_of_all_countries(link)
    add_ontologies(countries_lists, graph)
    graph.serialize(string, format="nt")


def list_of_all_countries(link):
    res = requests.get(link)
    doc = lxml.html.fromstring(res.content)
    list_of_countries_string = []
    list_of_countries_uri = []
    for t in doc.xpath("/descendant::table[position()=4]//tr//td[position()=1]/descendant::a[position()=1]/@href"):
        list_of_countries_uri.append(url + t)
    return list_of_countries_uri

def get_country_name(link):
    if "wiki/" not in link:
        return "None"
    country_name = link.split("wiki/")
    name = country_name[1]
    return name

def add_ontologies(countries_list_uri, graph):
    for i in range(len(countries_list_uri)):
        res = requests.get(countries_list_uri[i])
        doc = lxml.html.fromstring(res.content)
        country_name = get_country_name(countries_list_uri[i])
        country_ontology(graph,country_name)
        capital_ontology(doc, graph, country_name)
        area_ontology(doc, graph, country_name)
        population_ontology(doc, graph, country_name)
        government_ontology(doc, graph, country_name)
        president_uri = president_href(doc, graph, country_name)
        prime_minister_uri = prime_minister_href(doc, graph, country_name)
        president_name = presidant_ontology(doc, graph, country_name,president_uri)
        prime_minister_name = prime_minister_ontology(doc, graph, country_name,prime_minister_uri)
        born_ontology(president_uri,president_name,graph)
        born_ontology(prime_minister_uri,prime_minister_name, graph)

def born_ontology(uri, name, graph):
    if uri=="None" or name =="None":
        return
    res = requests.get(url+uri)
    doc = lxml.html.fromstring(res.content)
    date_of_birth = ""
    for t in doc.xpath("/descendant::table[@class='infobox vcard']//th[contains(text(),'Born')]/following-sibling::td[position()=1]//span[position()=1]/text()"):
        t = t.replace(" ", "_")
        t = t.replace("\n", "_")
        date_of_birth+= t
    if len(date_of_birth) and has_number(date_of_birth):
        graph.add((rdflib.URIRef(url+"/@"+name), rdflib.URIRef(url + "/Born"),
                   rdflib.URIRef(url + "/@"+date_of_birth)))
        return
    else:
        date_of_birth = ""
        for t in doc.xpath(
                "/descendant::table[@class='infobox vcard']//th[contains(text(),'Born')]/following-sibling::td[position()=1]/text()[position()=1]"):
            t = t.replace(" ", "_")
            t = t.replace("\n", "_")
            date_of_birth += t
        if len(date_of_birth) and has_number(date_of_birth) > 0:
            graph.add((rdflib.URIRef(url+"/@"+name), rdflib.URIRef(url + "/Born"),
                       rdflib.URIRef(url + "/@"+date_of_birth)))
            return


def special_case(graph,doc,name,word):
    if "city-state" in word:
        for t in doc.xpath(
                "/descendant::table[@class='infobox geography vcard']//th[contains(text(),'Capital')]/following-sibling::td[position()=1]//text()[position()=1]"):
            t = t.replace(" ", "_")
            t = t.replace("\n", "_")
            graph.add(
                (rdflib.URIRef(url + "/@" + name), rdflib.URIRef(url + "/Capital"),
                 rdflib.URIRef(url + "/@" + t)))
            return
    if "de_jure" in word:
        for t in doc.xpath(
                "/descendant::table[@class='infobox geography vcard']//th[contains(text(),'Capital')]/following-sibling::td[position()=1]/descendant::a[position()=2]/text()"):
            t = t.replace(" ", "_")
            t = t.replace("\n", "_")
            graph.add(
                (rdflib.URIRef(url + "/@" + name), rdflib.URIRef(url + "/Capital"),
                 rdflib.URIRef(url + "/@" + t)))
            return
    if "Singapore" in name:
        for t in doc.xpath(
                "/descendant::table[@class='infobox geography vcard']//th[contains(text(),'Capital')]/following-sibling::td[position()=1]/text()[position()=1]"):
            graph.add((rdflib.URIRef(url + "/@" + name), rdflib.URIRef(url + "/Capital"),
                       rdflib.URIRef(url + t)))
    if "pura_Kotte" in word:
        for j in doc.xpath(
                "/descendant::table[@class='infobox geography vcard']//th[contains(text(),'Capital')]/following-sibling::td[position()=1]/descendant::a[position()=3]/text()"):
            j = word+",_"+j.replace(" ","_")
            graph.add((rdflib.URIRef(url + "/@" + name), rdflib.URIRef(url + "/Capital"),
                       rdflib.URIRef(url + j)))



def has_number(word):
    return any(char.isdigit() for char in word)

def capital_ontology(doc, graph, countries_list_string):
    flag = False
    for t in doc.xpath(
            "/descendant::table[@class='infobox geography vcard']//th[contains(text(),'Capital')]"):
            flag = True
    if not flag:
        graph.add((rdflib.URIRef(url+"/@"+countries_list_string), rdflib.URIRef(url + "/Capital"),
                   rdflib.URIRef(url + "/None")))
        return
    for t in doc.xpath(
            "/descendant::table[@class='infobox geography vcard']//th[contains(text(),'Capital')]/following-sibling::td[position()=1]/descendant::a[position()=1]/text()"):
        if "[" in t or "None" in t:
            if "Singapore" in countries_list_string:
                special_case(graph,doc,countries_list_string,t)
                return
            graph.add((rdflib.URIRef(url+"/@"+countries_list_string), rdflib.URIRef(url + "/Capital"),
                       rdflib.URIRef(url + "/None")))
            return
        else:
            t = t.replace(" ", "_")
            t = t.replace("\n", "_")
            if "de_jure" not in t and "city-state" not in t and "pura_Kotte" not in t:
                graph.add(
                (rdflib.URIRef(url+"/@"+countries_list_string), rdflib.URIRef(url + "/Capital"), rdflib.URIRef(url + "/@" + t)))
                return
            if "city-state" in t:
                special_case(graph,doc,countries_list_string,t)
                return
            if "de_jure" in t:
                special_case(graph,doc,countries_list_string,t)
                return
            if "pura_Kotte" in t:
                special_case(graph,doc,countries_list_string,t)
                return
    for t in doc.xpath(
        "/descendant::table[@class='infobox geography vcard']//th[contains(text(),'Capital')]/following-sibling::td[position()=1]//text()[position()=1]"):
        t = t.replace(" ", "_")
        t = t.replace("\n", "_")
        if t != "_":
            graph.add(
            (rdflib.URIRef(url+"/@"+countries_list_string), rdflib.URIRef(url + "/Capital"), rdflib.URIRef(url + "/@" + t)))
            return
    for t in doc.xpath(
        "/descendant::table[@class='infobox geography vcard']//th[contains(text(),'Capital')]/../following-sibling::td[position()=1]//text()[position()=1]"):
        t = t.replace(" ", "_")
        t = t.replace("\n", "_")
        if t != "_":
            graph.add(
            (rdflib.URIRef(url+"/@"+countries_list_string), rdflib.URIRef(url + "/Capital"), rdflib.URIRef(url + "/@" + t)))
            return




def country_ontology(graph, country_name):
    graph.add(
        (rdflib.URIRef(url +"/@"+ country_name), rdflib.URIRef(url + "/Is"), rdflib.URIRef(url + "/country")))


def area_ontology(doc, graph, countries_list_string):
    for t in doc.xpath(
            "/descendant::table[@class='infobox geography vcard']//a[contains(text(),'Area')]/../../following-sibling::tr[position()=1]/td/text()[position()=1]"):

        if "km" not in t:
            t = t + " km"
        t = t.replace(" ", "_")
        t = t.replace("\n", "_")
        t = t.replace(chr(ord(" ")), "_")
        graph.add((rdflib.URIRef(url+"/@"+countries_list_string), rdflib.URIRef(url + "/Area"),
                   rdflib.URIRef(url + "/@" + t)))
        return
    for t in doc.xpath(
            "/descendant::table[@class='infobox geography vcard']//th[contains(text(),'Area')]/../following-sibling::tr[position()=1]/td/text()[position()=1]"):
        if "km" not in t:
            t = t + " km"
        t = t.replace(" ", "_")
        t = t.replace("\n", "_")
        t = t.replace(chr(ord(" ")), "_")
        graph.add((rdflib.URIRef(url+"/@"+countries_list_string), rdflib.URIRef(url + "/Area"),
                   rdflib.URIRef(url + "/@" + t)))
        return
    for t in doc.xpath(
            "/descendant::table[@class='infobox vcard']//th[contains(text(),'Area') and position()=1]/../td/text()[position()=1]"):
        if "km" not in t:
            t = t + " km"
        t = t.replace(" ", "_")
        t = t.replace("\n", "_")
        t = t.replace(chr(ord(" ")), "_")
        graph.add((rdflib.URIRef(url+"/@"+countries_list_string), rdflib.URIRef(url + "/Area"),
                   rdflib.URIRef(url + "/@" + t)))
        return


def population_ontology(doc, graph, countries_list_string):
    for t in doc.xpath(
            "/descendant::table[@class='infobox geography vcard']//a[contains(text(),'Population')]/../../following-sibling::tr[position()=1]/td//text()[position()=1]"):
        t = t.replace(" ", "")
        t = t.replace("\n", "_")
        if "(" == t:
            for j in doc.xpath(
                    "/descendant::table[@class='infobox geography vcard']//a[contains(text(),'Population')]/../../following-sibling::tr[position()=1]/td//li[position()=1]/text()[position()=1]"):
                j = j.replace(" ", "")
                j = j.replace(chr(ord("	")),"_")
                graph.add((rdflib.URIRef(url+"/@"+countries_list_string), rdflib.URIRef(url + "/Population"),
                           rdflib.URIRef(url + "/@" + j)))
                return
        if ("(") in t:
            t = t[:t.index("(")]
        t = t.replace(chr(ord("	")), "_")
        if t != "_":
            graph.add((rdflib.URIRef(url+"/@"+countries_list_string), rdflib.URIRef(url + "/Population"),
                           rdflib.URIRef(url + "/@" + t)))
            return
    for t in doc.xpath(
            "/descendant::table[@class='infobox vcard']//th[contains(text(),'Population')]/../td[position()=1]/text()[position()=1]"):
        t = t.replace(" ", "")
        t = t.replace("\n", "_")
        graph.add((rdflib.URIRef(url+"/@"+countries_list_string), rdflib.URIRef(url + "/Population"),
                           rdflib.URIRef(url + "/@" + t)))
        return

    for t in doc.xpath(
            "/descendant::table[@class='infobox geography vcard']//th[contains(text(),'Population')]/../following-sibling::tr[position()=1]/td/text()[position()=1]"):
        t = t.replace(" ", "")
        t = t.replace("\n", "_")
        t = t.replace(chr(ord("	")), "_")
        graph.add((rdflib.URIRef(url+"/@"+countries_list_string), rdflib.URIRef(url + "/Population"),
                           rdflib.URIRef(url + "/@" + t)))
        return


def government_ontology(doc, graph, countries_list_string):
    string_government = ""
    not_contains = "[not(contains(.,'1')) and not(contains(.,'2')) and not(contains(.,'3')) and not(contains(.,'4')) and not(contains(.,'5')) and not(contains(.,'6')) and not(contains(.,'7')) and not(contains(.,'8')) and not(contains(.,'9')) and not(contains(.,'[a]')) and not(contains(.,'[b]'))]"
    for t in doc.xpath(
            "/descendant::table[@class='infobox geography vcard']//text()[contains(.,'Government') and not(contains(.,'seat'))]/ancestor::*[self::th]/following-sibling::td[position()=1]//text()"+not_contains):

        string_government += t + ","
    string_government = string_government.replace(" ", "_")
    string_government = string_government.replace("\n", "_")
    graph.add((rdflib.URIRef(url+"/@"+countries_list_string), rdflib.URIRef(url + "/Government"),
               rdflib.URIRef(url + "/@" + string_government)))


def presidant_ontology(doc, graph, countries_list_string,president_uri):
    if "None" in president_uri:
        return "None"
    if "wiki/" not in president_uri:
        return "None"
    name = president_uri.split("wiki/")
    graph.add((rdflib.URIRef(url+"/@"+countries_list_string), rdflib.URIRef(url + "/President"),
               rdflib.URIRef(url + "/@" + name[1])))
    graph.add((rdflib.URIRef(url + "/@" + name[1]), rdflib.URIRef(url + "/job"),
                   rdflib.URIRef(url + "/President")))
    return name[1]


def president_href(doc, graph, countries_list_string):
    list_of_results =list()
    for t in doc.xpath(
            "/descendant::table[@class='infobox geography vcard']//a[contains(text(),'President') and not(contains(text(),'Vice')) and not(contains(text(),'Court')) and not(contains(text(),'Storting'))]/../../following-sibling::td[position()=1]//a[position()=1]/@href[position()=1]"):
        t = t.replace(" ", "_")
        t = t.replace("\n", "_")
        list_of_results.append(t)
    if len(list_of_results)>0:
        return list_of_results[0]
    else:
        return "None"

def special_case_href(graph,doc,countries_list_string):
    for t in doc.xpath(
            "/descendant::table[@class='infobox geography vcard']//a[text()='Prime Minister']/../../../following-sibling::td[position()=1]//a[position()=1]/@href[position()=1]"):
        t = t.replace(" ", "_")
        t = t.replace("\n", "_")
        return t


def prime_minister_href(doc, graph, countries_list_string):
    list_of_results =list()
    if "Guinea-Bissau" in countries_list_string:
        result = special_case_href(graph,doc,countries_list_string)
        return result
    for t in doc.xpath(
            "//tr[./th/div//a[contains(" \
                       "translate(text()[1], 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'prime minister')]]" \
                       "/td//a/@href[1]"):
        t = t.replace(" ", "_")
        t = t.replace("\n", "_")
        list_of_results.append(t)
    if len(list_of_results)>0:
        return list_of_results[0]
    list_yea.append(countries_list_string)
    return "None"

def prime_minister_ontology(doc, graph, countries_list_string, prime_uri):
    if "None" in prime_uri:
        return "None"
    if "wiki/" not in prime_uri:
        return "None"
    name = prime_uri.split("wiki/")
    graph.add((rdflib.URIRef(url+"/@"+countries_list_string), rdflib.URIRef(url + "/Prime_minister"),rdflib.URIRef(url + "/@" + name[1])))
    graph.add((rdflib.URIRef(url + "/@"+name[1]), rdflib.URIRef(url + "/job"),rdflib.URIRef(url + "/Prime_minister")))
    return name[1]


def who_query(string,graph):
    if "president" in string:
        country = string[5:]
        country = "_".join(country)
        x = graph.query("select ?president where \
                        { ?country <https://en.wikipedia.org/President> ?president\
                        filter (contains(lcase(str(?country)),\""+country[:len(country)-1].lower()+"\"))}")
        for i in x:
            answer = str(i).replace(")", "@")
            answer = answer.split("@")
            answer = answer[1].replace("'","")
            print(answer.replace("_"," "))
        return
    if "prime" in string:
        country = string[6:]
        country = "_".join(country)
        x = graph.query("select ?prime where \
                        { ?country <https://en.wikipedia.org/Prime_minister> ?prime\
                        filter (contains(lcase(str(?country)),\""+country[:len(country)-1].lower()+"\"))}")
        for i in list(x):
            answer = str(i).replace(")", "@")
            answer = answer.split("@")
            answer = answer[1].replace("'","")
            print(answer.replace("_"," "))
        return
    else:
        list_of_jobs = list()
        person = string[2:]
        person = "_".join(person)
        x = graph.query("select ?job?country where \
                        { ?name <https://en.wikipedia.org/job> ?job. \
                        ?country ?job ?name \
                        filter (contains(lcase(str(?name)),\""+person[:len(person)-1].lower()+"\"))}")
        for i in list(x):
            list_of_jobs.append(i)
        print_pretty(list_of_jobs)
        return

def print_pretty(list_of_jobs):
    president_list = list()
    prime_list =list()
    for i in list_of_jobs:
        if "President" in i[0]:
            president_list.append(i[1])
        if "Prime_minister" in i[0]:
            prime_list.append(i[1])
    string_president= "President of : "
    string_prime = "prime minister of :"
    if len(president_list)>0:
        for i in president_list:
            country = str(i).split("@")
            country = country[1].replace("_"," ")
            string_president += country + ", "
        print(string_president)
    if len(prime_list)>0:
        for i in prime_list:
            country = str(i).split("@")
            country = country[1].replace("_"," ")
            string_prime += country + ", "
        print(string_prime)




def what_query(string, graph):
    country = string[5:]
    country = "_".join(country)
    if "population" in string:
        x = graph.query("select ?pop?country where \
                        { ?country <https://en.wikipedia.org/Population> ?pop.\
                          filter (contains(lcase(str(?country)),\""+country[:len(country)-1].lower()+"\"))}")
        for i in list(x):
            answer = str(i).replace(")","@")
            answer = answer.split("@")
            answer = answer[1].replace("'", "")
            print(answer.replace("_", " "))
        return
    if "area" in string:
        x = graph.query("select ?area where \
                        { ?country <https://en.wikipedia.org/Area> ?area.\
                          filter (contains(lcase(str(?country)),\""+country[:len(country)-1].lower()+"\"))}")
        for i in list(x):
            answer = str(i).replace(")","@")
            answer = answer.split("@")
            answer = answer[1].replace("'","")
            answer.replace(")","")
            answer.replace("(", "")
            print(answer.replace("_"," "))
        return
    if "capital"in string:
        x = graph.query("select ?city where \
                        { ?country <https://en.wikipedia.org/Capital> ?city.\
                          filter (contains(lcase(str(?country)),\""+country[:len(country)-1].lower()+"\"))}")
        for i in list(x):
            answer = str(i).replace(")","@")
            answer = answer.split("@")
            answer = answer[1].replace("'", "")
            print(answer.replace("_", " "))
        return
    if "government" in string:
        x = graph.query("select ?gover where \
                        { ?country <https://en.wikipedia.org/Government> ?gover.\
                          filter (contains(lcase(str(?country)),\""+country[:len(country)-1].lower()+"\"))}")
        for i in list(x):
            answer = str(i).replace(")","@")
            answer = answer.split("@")
            answer = answer[1].replace("'", "")
            print(answer.replace("_", " "))
        return


def when_query(string,graph):
    if "president" in string:
        country = string[5:len(string)-1]
        country = "_".join(country)
        x = graph.query("select ?date where \
                        { ?country <https://en.wikipedia.org/President> ?president.\
                          ?president <https://en.wikipedia.org/Born> ?date.\
                          filter (contains(lcase(str(?country)),\""+country.lower()+"\"))}")
        for i in list(x):
            answer = str(i).replace("_","@")
            answer = answer.split("@")
            answer = answer[2].replace("_"," ")
            answer= answer.replace(")","")
            answer = answer.replace("(", "")
            print(answer)
        return
    if "prime" in string:
        country = string[6:len(string) - 1]
        country = "_".join(country)
        x = graph.query("select ?date where \
                        { ?country <https://en.wikipedia.org/Prime_minister> ?prime.\
                          ?prime <https://en.wikipedia.org/Born> ?date.\
                           filter (contains(lcase(str(?country)),\""+country.lower()+"\"))}")
        for i in list(x):
            answer = str(i).replace("_","@")
            answer = answer.split("@")
            answer = answer[2].replace("_"," ")
            answer= answer.replace(")","")
            answer = answer.replace("(", "")
            print(answer)
        return

def question(string):
    graph = rdflib.Graph()
    graph.parse("ontology.nt", format="nt")
    string_list = string.split(" ")
    first_word = string_list[0]
    if first_word == 'Who':
        who_query(string_list,graph)
    if first_word =="What":
        what_query(string_list,graph)
    if first_word =="When":
        when_query(string_list,graph)


def create(string):
    create_ontology("https://en.wikipedia.org/wiki/List_of_countries_by_population_(United_Nations)",string)

def main():
    question("Who is the prime minister of united Kingdom?")
    question("Who is the president of Italy?")
    question("What is the capital of Canada?")
    question("What is the area of Fiji?")
    question("What is the population of democratic Republic of the Congo?")
    question("What is the government of Eswatini?")
    question("When was the president of south Korea born?")
    question("When was the prime minister of new zealand born?")
    question("Who is donald trump?")
    question("Who is Kyriakos Mitsotakis?")
    question("What is the capital of Central African Republic?")
    create("ontology.nt")
    for j in list_yea:
        print(j)



if __name__ == "__main__":
	first_argv = sys.argv[1]
	if "create" in first_argv:
		create(sys.argv[2])
	if "question" in first_argv:
		question(str(sys.argv[2]))







