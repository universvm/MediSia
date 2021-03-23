import { Component, OnInit, Inject } from '@angular/core';
import { SearchData } from 'src/app/search-page/search-page.component';
import { MAT_DIALOG_DATA } from '@angular/material/dialog';
import { SearchService } from 'src/app/search.service';
import { MatSelectionListChange } from '@angular/material/list';

@Component({
  selector: 'app-pubyear-filter-modal',
  templateUrl: './pubyear-filter-modal.component.html',
  styleUrls: ['./pubyear-filter-modal.component.scss']
})
export class PubyearFilterModalComponent implements OnInit {
  years: Set<number>;
  searchData: SearchData | null;
  includedYears: number[] = [];
  originalYears: number[] = [];

  //filter: SolutionFilter = INITIALIZE_LATER;
  //flightsData: travel.matrix.IResult = INITIALIZE_LATER;

  //private unsubscribers: (() => void)[] = [];

  constructor(
    @Inject(MAT_DIALOG_DATA) public data: string[],
    private searchService: SearchService,
  ) { 
    this.years = this.searchService.pubyears;
    this.searchData = this.searchService.searchData;
    if (this.searchService.searchData) {
      this.includedYears = this.searchService.searchData.pubyear ? this.searchService.searchData.pubyear : [];
      this.originalYears = this.searchService.searchData.pubyear ? this.searchService.searchData.pubyear : [];
    }
  }

  ngOnInit() { }

  ngOnDestroy() { }

  onSelChange(event: MatSelectionListChange) {
    const includedYears = new Set(event.source.options.filter(o => o.selected).map(o => o.value));
    this.searchService.searchData!.pubyear = [...this.includedYears];
    this.includedYears = this.searchService.searchData!.pubyear ? this.searchService.searchData!.pubyear : [];
    console.log(this.searchService.searchData!.pubyear);
  }

  applyFilters() {
    console.log(this.searchService.searchData);
  }

  cancelFilters() {
    this.searchService.searchData!.pubyear = this.originalYears;
    console.log(this.searchService.searchData!.pubyear);
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
