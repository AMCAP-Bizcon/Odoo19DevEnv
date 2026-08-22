/** @odoo-module */

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, useState, markup } from "@odoo/owl";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";
import { user } from "@web/core/user";

export class FlashcardReview extends Component {
    static template = "kms_mastery.FlashcardReview";
    static props = {
        ...standardActionServiceProps,
    };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        
        this.state = useState({
            cards: [],
            currentIndex: 0,
            isFlipped: false,
            loading: true,
        });

        onWillStart(async () => {
            await this.loadCards();
        });
    }

    async loadCards() {
        // Fetch pending flashcards for the current user
        const today = new Date();
        const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
        
        this.state.cards = await this.orm.searchRead(
            "kms.user.flashcard",
            [
                "&",
                ["user_id", "=", user.userId],
                "|",
                ["next_review_date", "<=", todayStr],
                ["next_review_date", "=", false]
            ],
            ["id", "front", "back", "name"]
        );
        this.state.loading = false;
        
        // Markup HTML fields
        for (const card of this.state.cards) {
            card.frontMarkup = markup(card.front || "");
            card.backMarkup = markup(card.back || "");
        }
    }

    get currentCard() {
        if (this.state.currentIndex < this.state.cards.length) {
            return this.state.cards[this.state.currentIndex];
        }
        return null;
    }

    flipCard() {
        if (!this.state.isFlipped) {
            this.state.isFlipped = true;
        }
    }

    async rateCard(rating) {
        if (!this.currentCard) return;
        
        const cardId = this.currentCard.id;
        
        // Rating values match Python backend: 1=Again, 2=Hard, 3=Good, 4=Easy
        let actionMethod = "action_rate_again";
        if (rating === 2) actionMethod = "action_rate_hard";
        if (rating === 3) actionMethod = "action_rate_good";
        if (rating === 4) actionMethod = "action_rate_easy";
        
        await this.orm.call("kms.user.flashcard", actionMethod, [cardId]);
        
        // Flip back first
        this.state.isFlipped = false;
        
        // Wait briefly for flip animation to hide the back side before changing text
        setTimeout(() => {
            this.state.currentIndex++;
        }, 150);
    }
}

registry.category("actions").add("kms_mastery.flashcard_review", FlashcardReview);
