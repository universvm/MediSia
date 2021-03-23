import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PubyearFilterModalComponent } from './pubyear-filter-modal.component';

describe('PubyearFilterModalComponent', () => {
  let component: PubyearFilterModalComponent;
  let fixture: ComponentFixture<PubyearFilterModalComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ PubyearFilterModalComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(PubyearFilterModalComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
