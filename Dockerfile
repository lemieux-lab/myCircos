FROM centos:7.2.1511
MAINTAINER IRIC Bioinformatics Platform <mycircos.iric.ca>
WORKDIR /mycircos
ENV PATH=/mycircos/current/bin:$PATH

# Circos
RUN yum install -y tar curl
RUN curl http://circos.ca/distribution/circos-0.69.tgz | tar xz 
RUN ln -s circos-0.69 current

# GCC (for List::MoreUtils)
RUN yum install -y gcc

# Perl
RUN yum install -y perl 
RUN yum install -y perl-Clone perl-Config-Tiny perl-Data-Dumper perl-Digest-MD5 perl-Font-TTF perl-GD perl-Params-Util perl-ExtUtils-MakeMaker
RUN yum install -y cpanminus
#RUN curl -L http://cpanmin.us | perl - App::cpanminus
RUN cpanm --force Config::General List::MoreUtils Math::Bezier
RUN cpanm Params::Validate Math::Round Math::VecStat Readonly Regexp::Common
RUN cpanm SVG Set::IntSpan Statistics::Basic Text::Format Time::HiRes

# Python
RUN curl https://bootstrap.pypa.io/get-pip.py | python
RUN pip install celery

# REDIS
RUN curl http://download.redis.io/releases/redis-3.0.7.tar.gz | tar xz 
RUN cd redis-3.0.7 && make

# Writeable data folder
RUN mkdir var && chown 1169:100 var

# MyCircos
RUN yum install -y git
RUN pip install flask flask-sqlalchemy flask-login sqlalchemy-migrate requests passlib
RUN pip install redis

# Networking
EXPOSE 8090


# Version 2 -- Manually done

#RUN git clone http://gitlab.iric.ca/mycircos/mycircos.git
#RUN rsync -av gendrop@binsrv4.iric.ca:/u/gendrop/project/mycircos/mycircos .
#RUN chown -R 1169:100 var mycircos/
#RUN python db_create.py

#RUN /mycircos/redis-3.0.7/src/redis-server &
#RUN C_FORCE_ROOT=1 celery -A app.celery_tasks.celery_app worker -C --concurrency=2 &
#RUN python run.py 
