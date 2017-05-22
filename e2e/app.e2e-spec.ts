import { FollowTheInsidersPage } from './app.po';

describe('follow-the-insiders App', () => {
  let page: FollowTheInsidersPage;

  beforeEach(() => {
    page = new FollowTheInsidersPage();
  });

  it('should display message saying app works', () => {
    page.navigateTo();
    expect(page.getParagraphText()).toEqual('app works!');
  });
});
