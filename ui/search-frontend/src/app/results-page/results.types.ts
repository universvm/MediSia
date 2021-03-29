export type ResultsJson = {
    "categories": string[];
    //"authors": string[];
    "journals": string[];
    "pubyears": number[];
    "results": 
      {
        "doi": string,
        "year": number,
        "genre": string,
        "is_oa": boolean,
        "title": string,
        "doi_url": string,
        "updated": string,
        "oa_status": string,
        "publisher": string,
        "z_authors": 
            {
                "given": string,
                "family": string,
                "sequence": string,
            }[],
        "is_paratext": boolean,
        "journal_name": string,
        "oa_locations": string[],
        "data_standard": number,
        "journal_is_oa": boolean,
        "journal_issns": string,
        "journal_issn_l": string,
        "published_date": string,
        "best_oa_location": string | null,
        "first_oa_location": string | null,
        "journal_is_in_doaj": boolean,
        "has_repository_copy": boolean,
        "abstract": string,
        "abstract_source": string,
        "category": string,
      }[]
}

export type PaperJson = {
    "doi": string,
    "year": number,
    "genre": string,
    "is_oa": boolean,
    "title": string,
    "doi_url": string,
    "updated": string,
    "oa_status": string,
    "publisher": string,
    "z_authors": 
        {
            "given": string,
            "family": string,
            "sequence": string,
        }[],
    "is_paratext": boolean,
    "journal_name": string,
    "oa_locations": string[],
    "data_standard": number,
    "journal_is_oa": boolean,
    "journal_issns": string,
    "journal_issn_l": string,
    "published_date": string,
    "best_oa_location": string | null,
    "first_oa_location": string | null,
    "journal_is_in_doaj": boolean,
    "has_repository_copy": boolean,
    "abstract": string,
    "abstract_source": string,
    "category": string,
}

export type AuthorJson = {
    "given": string,
    "family": string,
    "sequence": string,
}

export class Results {
    categories: string[];
    //authors: string[];
    journals: string[];
    pubyears: number[];
    results: Paper[];

    constructor(resultsJson: ResultsJson) {
        this.categories = resultsJson.categories;
        //this.authors = resultsJson.authors;
        this.journals = resultsJson.journals;
        this.pubyears = resultsJson.pubyears;
        this.results = resultsJson.results.map(result => {return new Paper(result)})
    }
}
  
export class Paper {
    title: string;
    abstract: string;
    authors: Author[] | null;
    pubyear: number;
    journal: string;
    url: string;
    topic: string;

    constructor(paperJson: PaperJson) {
        this.title = paperJson.title;
        this.abstract = this.truncateChar(paperJson.abstract);
        this.authors = paperJson.z_authors? paperJson.z_authors.map(author => new Author(author)) : null;
        this.pubyear = paperJson.year;
        this.journal = paperJson.journal_name;
        this.url = paperJson.doi_url;
        this.topic = paperJson.category;
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

export class Author {
    name: string;

    constructor(authorJson: AuthorJson) {
        this.name = authorJson.given + " " + authorJson.family;
    }
}