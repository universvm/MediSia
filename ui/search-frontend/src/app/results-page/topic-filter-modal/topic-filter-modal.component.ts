import { Component, OnInit, Inject } from '@angular/core';
import { SearchData } from 'src/app/search-page/search-page.component';
import { MAT_DIALOG_DATA } from '@angular/material/dialog';
import { SearchService } from 'src/app/search.service';
import { MatSelectionListChange } from '@angular/material/list';

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
    private searchService: SearchService,
  ) { 
    this.topics = this.searchService.topics;
    this.searchData = this.searchService.searchData;
    if (this.searchService.searchData) {
      this.includedTopics = this.searchService.searchData.category ? this.searchService.searchData.category : [];
      this.originalTopics = this.searchService.searchData.category ? this.searchService.searchData.category : [];
    }
  }

  ngOnInit() { }

  ngOnDestroy() { }

  onSelChange(event: MatSelectionListChange) {
    const includedTopics = new Set(event.source.options.filter(o => o.selected).map(o => o.value));
    this.searchService.searchData!.category = [...includedTopics];
    this.includedTopics = this.searchService.searchData!.category ? this.searchService.searchData!.category : [];
    console.log(this.searchService.searchData!.category);
  }

  applyFilters() {
    console.log(this.searchService.searchData);
  }

  cancelFilters() {
    this.searchService.searchData!.journal = this.originalTopics;
    console.log(this.searchService.searchData!.category);
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
