import { Component, OnInit, Inject } from '@angular/core';
import { MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MatSelectionListChange } from '@angular/material/list';
import { SearchData } from 'src/app/search-page/search-page.component';
import { ResultsService } from 'src/app/results.service';
import { SearchService } from 'src/app/search.service';

@Component({
  selector: 'app-journal-filter-modal',
  templateUrl: './journal-filter-modal.component.html',
  styleUrls: ['./journal-filter-modal.component.scss']
})
export class JournalFilterModalComponent implements OnInit {
  journals: Set<string>;
  searchData: SearchData | null;
  includedJournals: string[] = [];
  originalJournals: string[] = [];

  //filter: SolutionFilter = INITIALIZE_LATER;
  //flightsData: travel.matrix.IResult = INITIALIZE_LATER;

  //private unsubscribers: (() => void)[] = [];

  constructor(
    @Inject(MAT_DIALOG_DATA) public data: string[],
    private resultsService: ResultsService,
    private searchService: SearchService,
  ) { 
    this.journals = this.resultsService.journals;
    this.searchData = this.searchService.searchData;
    if (this.searchService.searchData) {
      this.includedJournals = this.searchService.searchData.journals ? this.searchService.searchData.journals : [];
      this.originalJournals = this.searchService.searchData.journals ? this.searchService.searchData.journals : [];
    }
  }

  ngOnInit() { }

  ngOnDestroy() { }

  onSelChange(event: MatSelectionListChange) {
    const includedJournals = new Set(event.source.options.filter(o => o.selected).map(o => o.value));
    this.searchService.searchData!.journals = [...includedJournals];
    this.includedJournals = this.searchService.searchData!.journals ? this.searchService.searchData!.journals : [];
    console.log(this.searchService.searchData!.journals);
  }

  applyFilters() {
    console.log(this.searchService.searchData);
  }

  cancelFilters() {
    this.searchService.searchData!.journals = this.originalJournals;
    console.log(this.searchService.searchData!.journals);
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
