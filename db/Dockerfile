FROM postgres:16
COPY prepare.sql .
RUN chmod 444 /prepare.sql

CMD ["postgres"]
