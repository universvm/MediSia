import { ComponentFixture, TestBed } from '@angular/core/testing';

import { JournalFilterModalComponent } from './journal-filter-modal.component';

describe('JournalFilterModalComponent', () => {
  let component: JournalFilterModalComponent;
  let fixture: ComponentFixture<JournalFilterModalComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ JournalFilterModalComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(JournalFilterModalComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
