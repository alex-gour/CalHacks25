export class HttpClient {
  private readonly fetcher: { fetch: (request: Request) => Promise<Response> };

  constructor() {
    this.fetcher = this.resolveFetcher();
  }

  async fetch(request: Request): Promise<Response> {
    return this.fetcher.fetch(request);
  }

  private resolveFetcher(): { fetch: (request: Request) => Promise<Response> } {
    const modules = ["LensStudio:InternetModule", "LensStudio:RemoteServiceModule"];

    for (const moduleName of modules) {
      try {
        const candidate = require(moduleName);
        if (candidate && typeof candidate.fetch === "function") {
          print(`HttpClient using ${moduleName}`);
          return candidate;
        }
      } catch (error) {
        print(`HttpClient could not load ${moduleName}: ${error}`);
      }
    }

    throw new Error("HttpClient could not resolve a fetch-capable module");
  }
}
