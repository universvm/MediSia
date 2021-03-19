import { Component, OnInit } from '@angular/core';
import { FormControl, FormGroup, AbstractControl, ValidationErrors } from '@angular/forms';
import { Router } from '@angular/router';

export interface SearchData {
  readonly query: string | null;
  readonly author: string | null;
  readonly journal: string | null;
  readonly pubyear: string | null;
  readonly deepSearch: boolean;
}

@Component({
  selector: 'app-search-page',
  templateUrl: './search-page.component.html',
  styleUrls: ['./search-page.component.scss']
})
export class SearchPageComponent implements OnInit {

  searchForm = new FormGroup({
    query: new FormControl(null),
    author: new FormControl(null),
    journal: new FormControl(null),
    pubyear: new FormControl(null, [this.pubYearValidator]),
    deepSearch: new FormControl(false),
  });

  isAdvanced: boolean = false;
  isDeep: boolean = false;

  constructor(
    private router: Router,
  ) { }

  ngOnInit(): void {
  }

  onSubmit() {
    const value: SearchData = this.searchForm.value;

    console.log(value.query);
    console.log(value.author);
    console.log(value.journal);
    console.log(value.pubyear);
    console.log(value.deepSearch);

    // when sending to backend, atm if !isAdvanced, set those fields to null regardless of input

    this.router.navigate(['results']);
  }

  onAdvanced() {
    this.isAdvanced = !this.isAdvanced;
  }

  pubYearValidator(control: AbstractControl): ValidationErrors | null {
    const regex = RegExp(/^(\d){4}(( )?-( )?(\d){4})?( )?$/); //make regex handle year/rangeg
    const matches = regex.test(control.value);
    if (control.value === null || control.value === '') {
      return null;
    } else if (!matches) {
      return { invalidYear: true };
    } else {
      return null;
    }
  }

}
