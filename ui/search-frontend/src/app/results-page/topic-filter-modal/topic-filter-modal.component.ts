import { Component, OnInit, Inject } from '@angular/core';
import { SearchData } from 'src/app/search-page/search-page.component';
import { MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MatSelectionListChange } from '@angular/material/list';
import { ResultsService } from 'src/app/results.service';
import { SearchService } from 'src/app/search.service';

@Component({
  selector: 'app-topic-filter-modal',
  templateUrl: './topic-filter-modal.component.html',
  styleUrls: ['./topic-filter-modal.component.scss']
})
export class TopicFilterModalComponent implements OnInit {
  topics: Set<string>;
  searchData: SearchData | null;
  includedTopics: string[] = [];
  originalTopics: string[] = [];

  //filter: SolutionFilter = INITIALIZE_LATER;
  //flightsData: travel.matrix.IResult = INITIALIZE_LATER;

  //private unsubscribers: (() => void)[] = [];

  constructor(
    @Inject(MAT_DIALOG_DATA) public data: string[],
    private resultsService: ResultsService,
    private searchService: SearchService,
  ) { 
    this.topics = this.resultsService.categories;
    this.searchData = this.searchService.searchData;
    if (this.searchService.searchData) {
      this.includedTopics = this.searchService.searchData.categories ? this.makeListFromString(this.searchService.searchData.categories) : [];
      this.originalTopics = this.searchService.searchData.categories ? this.makeListFromString(this.searchService.searchData.categories) : [];
    }
  }

  makeListFromString(categories: string) {
    if (categories.includes(',')) {
      return categories.split(',');
    } else return [categories];
  }

  ngOnInit() { }

  ngOnDestroy() { }

  onSelChange(event: MatSelectionListChange) {
    const includedTopics = new Set(event.source.options.filter(o => o.selected).map(o => o.value));
    this.searchService.searchData!.categories = [...includedTopics].join();
    this.includedTopics = this.searchService.searchData!.categories ? this.makeListFromString(this.searchService.searchData!.categories) : [];
    console.log(this.searchService.searchData!.categories);
  }

  applyFilters() {
    console.log(this.searchService.searchData);
    this.resultsService.updateQuery({
      categories: this.searchService.searchData!.categories,
      type: "follow-up",
      propagate: true,
    });
  }

  cancelFilters() {
    this.searchService.searchData!.categories = this.originalTopics.join();
    console.log(this.searchService.searchData!.categories);
  }
  //isAllSelected(includedJournals = this.filter.includedJournals) {
    //return includedJournals === null || this.carrierList?.groups?.every(c => includedCarrierCodes.has(c.label.code));
  //}

  //deselectAll() {
    //this.data.updateFilter({
      //includedCarrierCodes: new Set(),
    //});
  //}

  //selectAll() {
    //this.data.updateFilter({
      //includedCarrierCodes: null,
    //});
  //}

}
