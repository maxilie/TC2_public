import {Component} from '@angular/core';

enum ProgramVisualType {
    PRICE_GRAPH,
    BREAKOUT1_SETUP,
    SWING_SETUP
}

@Component({
    selector: 'app-visuals-content',
    templateUrl: './visuals-content.component.html',
    styleUrls: ['./visuals-content.component.less'],
})

export class VisualsContentComponent {
    // The visual to show right now
    selectedVisual = ProgramVisualType.PRICE_GRAPH;

    // A reference to ProgramVisualType for use in html
    visualType = ProgramVisualType;

    public visualTypes(): ProgramVisualType[] {
        const types = [];
        for (let i = 0; i < Object.keys(ProgramVisualType).length / 2; i++) {
            types.push(ProgramVisualType[ProgramVisualType[i]]);
        }
        return types;
    }

    private selectVisual(visualType: ProgramVisualType) {
        this.selectedVisual = visualType;
    }

    private selectPrevVisual() {
        let index = this.selectedVisual;
        if (index > 0) {
            this.selectedVisual = ProgramVisualType[ProgramVisualType[index - 1]];
        }
    }

    private selectNextVisual() {
        let index = this.selectedVisual;
        if (index < Object.keys(ProgramVisualType).length / 2 - 1) {
            this.selectedVisual = ProgramVisualType[ProgramVisualType[index + 1]];
        }
    }
}
