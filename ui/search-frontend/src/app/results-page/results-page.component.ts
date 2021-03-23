import { Component, OnInit } from '@angular/core';
import testdata from '../../assets/testdata.json';
import { Results, Paper } from './results.types';
import { SearchService } from '../search.service';
import { MatDialog } from '@angular/material/dialog';
import { JournalFilterModalComponent } from './journal-filter-modal/journal-filter-modal.component';
import { PubyearFilterModalComponent } from './pubyear-filter-modal/pubyear-filter-modal.component';
import { TopicFilterModalComponent } from './topic-filter-modal/topic-filter-modal.component';

@Component({
  selector: 'app-results-page',
  templateUrl: './results-page.component.html',
  styleUrls: ['./results-page.component.scss']
})
export class ResultsPageComponent implements OnInit {
  results: Results | null;
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
    private searchService: SearchService,
    public dialog: MatDialog, 
  ) {
    this.results = new Results(testdata);
    this.title = this.createTitle();
  }

  createTitle() {
    if (this.searchService.searchData === null) return "";
    var temp = "\"" + this.searchService.searchData!.query;
    if (this.searchService.searchData!.category !== null) temp = temp + ", " + this.searchService.searchData!.category;
    if (this.searchService.searchData!.author !== null) temp = temp + ", " + this.searchService.searchData!.author;
    if (this.searchService.searchData!.journal !== null) temp = temp + ", " + this.searchService.searchData!.journal;
    if (this.searchService.searchData!.pubyear !== null) temp = temp + ", " + this.searchService.searchData!.pubyear;
    return temp + "\"";
  }

  getColour(index: number) {
    const topic = this.results!.results[index].topic;
    return this.colours[topic];
  }

  filterJournals() {
    const dialogRef = this.dialog.open(JournalFilterModalComponent, {
      width: '900px',
      data: {}
    });
    console.log('hi');
  }

  filterTopics() {
    const dialogRef = this.dialog.open(TopicFilterModalComponent, {
      width: '900px',
      data: {}
    });
    console.log('hi');
  }

  filterYears() {
    const dialogRef = this.dialog.open(PubyearFilterModalComponent, {
      width: '900px',
      data: {}
    });
    console.log('hi');
  }

  ngOnInit(): void {}

}