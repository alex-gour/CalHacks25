export type HttpFetchModule = {
  fetch: (request: Request) => Promise<Response>;
};

export class HttpClient {
  private fetcher?: HttpFetchModule;

  setFetcher(module?: HttpFetchModule | null): void {
    if (module && typeof module.fetch === "function") {
      this.fetcher = module;
    }
  }

  async fetch(request: Request): Promise<Response> {
    const fetcher = this.ensureFetcher();
    return fetcher.fetch(request);
  }

  private ensureFetcher(): HttpFetchModule {
    if (this.fetcher) {
      return this.fetcher;
    }

    const modules = [
      "LensStudio:InternetModule",
      "InternetModule",
      "LensStudio:RemoteServiceModule",
      "RemoteServiceModule",
    ];

    for (const moduleName of modules) {
      try {
        const candidate = require(moduleName);
        if (candidate && typeof candidate.fetch === "function") {
          print(`HttpClient using ${moduleName}`);
          this.fetcher = candidate as HttpFetchModule;
          return this.fetcher;
        }
      } catch (error) {
        // Module not available; try the next option.
      }
    }

    const globalFetch = (globalThis as any).fetch;
    if (typeof globalFetch === "function") {
      print("HttpClient using global fetch fallback");
      this.fetcher = { fetch: (req: Request) => globalFetch(req) };
      return this.fetcher;
    }

    throw new Error(
      "HttpClient could not resolve a fetch-capable module. Assign a Remote Service/Internet module via script input."
    );
  }
}
