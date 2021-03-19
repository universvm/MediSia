import { Component, OnInit } from '@angular/core';
import testdata from '../../assets/testdata.json';
import { Results, Paper } from './results.types';

@Component({
  selector: 'app-results-page',
  templateUrl: './results-page.component.html',
  styleUrls: ['./results-page.component.scss']
})
export class ResultsPageComponent implements OnInit {
  results: Results | null;

  constructor() {
    this.results = new Results(testdata);
  }

  ngOnInit(): void {}

}
