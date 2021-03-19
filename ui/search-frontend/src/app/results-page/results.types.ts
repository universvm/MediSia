export type ResultsJson = {
    "topics": string[];
    "authors": string[];
    "journals": string[];
    "pubyears": number[];
    "results": 
      {
        "title": string;
        "abstract": string;
        "authors": string[];
        "pubyear": number;
        "journal": string;
        "url": string;
        "topic": string;
      }[]
}

export type PaperJson = {
    "title": string;
    "abstract": string;
    "authors": string[];
    "pubyear": number;
    "journal": string;
    "url": string;
    "topic": string;
}

export class Results {
    topics: string[];
    authors: string[];
    journals: string[];
    pubyears: number[];
    results: Paper[];

    constructor(resultsJson: ResultsJson) {
        this.topics = resultsJson.topics;
        this.authors = resultsJson.authors;
        this.journals = resultsJson.journals;
        this.pubyears = resultsJson.pubyears;
        this.results = resultsJson.results.map(result => {return new Paper(result)})
    }
}
  
export class Paper {
    title: string;
    abstract: string;
    authors: string[];
    pubyear: number;
    journal: string;
    url: string;
    topic: string;

    constructor(paperJson: PaperJson) {
        this.title = paperJson.title;
        this.abstract = this.truncateChar(paperJson.abstract);
        this.authors = paperJson.authors;
        this.pubyear = paperJson.pubyear;
        this.journal = paperJson.journal;
        this.url = paperJson.url;
        this.topic = paperJson.topic;
    }  
    
    truncateChar(text: string): string {
        let charlimit = 300;
        if(!text) {
            return "No preview available";
        } else if(text.length <= charlimit) {
            return text;
        }
    
        let shortened = text.substring(0, charlimit) + "...";
        return shortened;
    }
}