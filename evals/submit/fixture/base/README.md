# acme-notify

A small notification sender used by the Acme back office. Messages are posted to the
upstream gateway; a tenant that sends too fast is throttled. Run `make test` before you
push, and `make lint` for a syntax pass. When the gateway is flaky you may recieve a
DeliveryError after the retries are exhausted.
