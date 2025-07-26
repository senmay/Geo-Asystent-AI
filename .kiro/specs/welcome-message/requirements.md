# Requirements Document

## Introduction

Ta funkcjonalność dodaje automatyczną wiadomość powitalną w oknie czatu, która pojawia się przy pierwszym otwarciu aplikacji. Wiadomość przedstawia asystenta GIS i wyjaśnia dostępne narzędzia, poprawiając doświadczenie użytkownika i ułatwiając rozpoczęcie pracy z systemem.

## Requirements

### Requirement 1

**User Story:** Jako użytkownik aplikacji GIS, chcę otrzymać wiadomość powitalną przy pierwszym otwarciu czatu, żeby wiedzieć kim jest asystent i jakie możliwości oferuje.

#### Acceptance Criteria

1. WHEN użytkownik otwiera aplikację po raz pierwszy THEN system SHALL wyświetlić wiadomość powitalną w oknie czatu
2. WHEN wiadomość powitalna jest wyświetlana THEN system SHALL przedstawić asystenta jako "Geo-Asystent AI"
3. WHEN wiadomość powitalna jest wyświetlana THEN system SHALL wyjaśnić główne możliwości systemu w języku polskim
4. WHEN wiadomość powitalna jest wyświetlana THEN system SHALL podać przykłady zapytań, które użytkownik może zadać

### Requirement 2

**User Story:** Jako użytkownik, chcę żeby wiadomość powitalna była wyświetlana tylko przy pierwszym otwarciu, żeby nie przeszkadzała mi przy kolejnych sesjach.

#### Acceptance Criteria

1. WHEN użytkownik odświeża stronę lub wraca do aplikacji THEN system SHALL NOT wyświetlać ponownie wiadomości powitalnej w tej samej sesji
2. WHEN użytkownik rozpoczyna nową sesję (nowa karta/okno przeglądarki) THEN system SHALL wyświetlić wiadomość powitalną
3. WHEN wiadomość powitalna została już wyświetlona THEN system SHALL pozwolić na normalne działanie czatu

### Requirement 3

**User Story:** Jako użytkownik, chcę żeby wiadomość powitalna była czytelna i profesjonalna, żeby zrozumieć jak korzystać z systemu.

#### Acceptance Criteria

1. WHEN wiadomość powitalna jest wyświetlana THEN system SHALL użyć przyjaznego i profesjonalnego tonu
2. WHEN wiadomość powitalna jest wyświetlana THEN system SHALL wymienić główne kategorie operacji GIS (działki, budynki, GPZ)
3. WHEN wiadomość powitalna jest wyświetlana THEN system SHALL podać 2-3 konkretne przykłady zapytań
4. WHEN wiadomość powitalna jest wyświetlana THEN system SHALL być sformatowana jako wiadomość od asystenta (nie systemowa notyfikacja)