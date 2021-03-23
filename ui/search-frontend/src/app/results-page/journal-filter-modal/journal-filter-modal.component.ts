import { Component, OnInit, Inject } from '@angular/core';
import { MAT_DIALOG_DATA } from '@angular/material/dialog';
import { SearchService } from 'src/app/search.service';
import { MatSelectionListChange } from '@angular/material/list';
import { SearchData } from 'src/app/search-page/search-page.component';

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
    private searchService: SearchService,
  ) { 
    this.journals = this.searchService.journals;
    this.searchData = this.searchService.searchData;
    if (this.searchService.searchData) {
      this.includedJournals = this.searchService.searchData.journal ? this.searchService.searchData.journal : [];
      this.originalJournals = this.searchService.searchData.journal ? this.searchService.searchData.journal : [];
    }
  }

  ngOnInit() { }

  ngOnDestroy() { }

  onSelChange(event: MatSelectionListChange) {
    const includedJournals = new Set(event.source.options.filter(o => o.selected).map(o => o.value));
    this.searchService.searchData!.journal = [...includedJournals];
    this.includedJournals = this.searchService.searchData!.journal ? this.searchService.searchData!.journal : [];
    console.log(this.searchService.searchData!.journal);
  }

  applyFilters() {
    console.log(this.searchService.searchData);
  }

  cancelFilters() {
    this.searchService.searchData!.journal = this.originalJournals;
    console.log(this.searchService.searchData!.journal);
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
