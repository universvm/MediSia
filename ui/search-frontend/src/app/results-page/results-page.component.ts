import { Component, OnInit, OnDestroy, Output } from '@angular/core';
import { Results, Paper, ResultsJson } from './results.types';
import { MatDialog } from '@angular/material/dialog';
import { JournalFilterModalComponent } from './journal-filter-modal/journal-filter-modal.component';
import { PubyearFilterModalComponent } from './pubyear-filter-modal/pubyear-filter-modal.component';
import { TopicFilterModalComponent } from './topic-filter-modal/topic-filter-modal.component';
import { ResultsService, SearchQuery } from '../results.service';
import { SearchService } from '../search.service';
import { tap, map, filter } from 'rxjs/operators';
import { ReplaySubject, Observable } from 'rxjs';
import { Router } from '@angular/router';
import { Debugout } from 'debugout.js';

@Component({
  selector: 'app-results-page',
  templateUrl: './results-page.component.html',
  styleUrls: ['./results-page.component.scss']
})
export class ResultsPageComponent implements OnInit, OnDestroy {
  readonly resultsData$ = new ReplaySubject<ResultsJson | null>(1);
  results: Observable<Paper[][]> = new Observable();
  numPages: number = 0;
  pages: Paper[][] = [];
  timeForSearch: number = 0;

  loading = true;

  private readonly unsubscribers: (() => void)[] = [];

  bugout = new Debugout();

  title: string = "";
  colours: {[topic: string]: string} = {
    "agriculture": "#00ccff",
    "anatomy": "#0099ff",
    "biochemistry": "#0066cc",
    "bioengineering": "#0033cc",
    "bioinformatics": "#00ff99",
    "biology": "#00cc66",
    "biophysics": "#00cc00",
    "botany": "#009900",
    "dental": "#ffcc00",
    "ecology": "#ff9900",
    "entomology": "#cc3300",
    "forestry": "#ff0000",
    "genetics": "#ff6600",
    "healthcare": "#cc0066",
    "medicine": "#ff0066",
    "microbiology": "#ff3399",
    "molecular": "#ff6699",
    "mycology": "#ff33cc",
    "neuroscience": "#cc33ff",
    "nursing": "#cc99ff",
    "nutrition": "#9999ff",
    "ornithology": "#9933ff",
    "pharmacy": "#6600cc",
    "psychiatry": "#3333ff",
    "virology": "#339966",
    "zoology": "#660066"
  }

  constructor(
    private resultsService: ResultsService,
    private searchService: SearchService,
    public dialog: MatDialog, 
    private router: Router,
  ) {
    this.title = this.createTitle();
  }

  markIrrelevant(paper: Paper) {
    paper.irrelevant = true;
    this.bugout.log(this.title + ": " + paper.title);
  }

  createTitle() {
    if (this.searchService.searchData === null) return "";
    var temp = "\"" + this.searchService.searchData!.query;
    if (this.searchService.searchData!.categories !== null) temp = temp + ", " + this.searchService.searchData!.categories;
    //if (this.searchService.searchData!.author !== null) temp = temp + ", " + this.searchService.searchData!.author;
    if (this.searchService.searchData!.journals !== null) temp = temp + ", " + this.searchService.searchData!.journals;
    if (this.searchService.searchData!.pubyears !== null) temp = temp + ", " + this.searchService.searchData!.pubyears;
    return temp + "\"";
  }

  ngOnInit() {
    this.checkIfComingFromSearch();
    let start = performance.now();
    const subscription = this.resultsService.result$.pipe(
      tap(() => this.loading = false),
    ).subscribe(this.resultsData$);
    this.unsubscribers.push(() => subscription.unsubscribe());

    this.results = this.resultsData$.pipe(
      filter((data): data is ResultsJson => data !== null),
      map(data => {
        if (this.timeForSearch === 0) {
          this.timeForSearch = Math.floor(performance.now() - start);
          this.bugout.log(this.title + ": " + this.timeForSearch + "ms");
        };
        return this.makePagesFromArray(new Results(data))
      }),
    );
  }

  /**
   * Checks that the user is coming from the search page. If the user has
   * navigated to this page directly, without going through the search page, it
   * redirects them to the search page. 
   */
  checkIfComingFromSearch() {
    if (this.searchService.searchData === null) {
      // the search data on the search service is not set, so the
      // user has not previously visited the search page
      this.router.navigate(['search']);
    }
  }

  makePagesFromArray(results: Results) {
    let papers = [];
    for (var i=1; i-1<(results.results.length/10); i++) {
      papers[i-1] = results.results.slice((i*10)-10, (i*10)-1);;
    }
    console.log(papers)
    return papers;
  }

  nextPage() {
    this.numPages = this.numPages + 1;
  }

  prevPage() {
    this.numPages = this.numPages - 1;
  }

  applyCategory(category: string) {
    this.searchService.searchData!.categories = category;
    this.resultsService.updateQuery({
      categories: this.searchService.searchData!.categories,
      type: "follow-up",
      propagate: true,
    });
    this.numPages = 0;
  }

  checkIfCategoryFilter() {
    if (this.searchService.searchData!.categories !== null) return false;
    else return true;
  }

  getColour(topic: string) {
    return this.colours[topic];
  }

  filterJournals() {
    const dialogRef = this.dialog.open(JournalFilterModalComponent, {
      width: '900px',
      data: {}
    });
  }

  filterTopics() {
    const dialogRef = this.dialog.open(TopicFilterModalComponent, {
      width: '900px',
      data: {}
    });
  }

  filterYears() {
    const dialogRef = this.dialog.open(PubyearFilterModalComponent, {
      width: '900px',
      data: {}
    });
  }

  ngOnDestroy() {
    this.unsubscribers.forEach(a => a());
    this.bugout.downloadLog();
  }

}

